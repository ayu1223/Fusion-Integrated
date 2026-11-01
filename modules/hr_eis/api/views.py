"""HTTP layer for HR-EIS: parse, authorise, delegate to services, serialise."""
from __future__ import annotations

from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.api.exceptions import ConflictError, NotFoundError, PermissionDeniedError
from fusion_auth.permissions import HasModuleGrant, HasPermission
from modules.hr_eis import contracts, models as m, selectors, services
from modules.hr_eis.api import serializers as s

MODULE = HasModuleGrant("hr_eis")

# -- permissions -------------------------------------------------------------
P_SERVICE_RECORD_VIEW = "hr_eis.service_record.view"
P_SERVICE_RECORD_MANAGE = "hr_eis.service_record.manage"
P_LEAVE_APPLY = "hr_eis.leave.apply"
P_LEAVE_VIEW_SELF = "hr_eis.leave.view_self"
P_LEAVE_VIEW = "hr_eis.leave.view"
P_LEAVE_DECIDE = "hr_eis.leave.decide"
P_APPRAISAL_SUBMIT = "hr_eis.appraisal.submit"
P_APPRAISAL_VIEW_SELF = "hr_eis.appraisal.view_self"
P_APPRAISAL_VIEW = "hr_eis.appraisal.view"
P_APPRAISAL_ASSIGN_REVIEWER = "hr_eis.appraisal.assign_reviewer"
P_APPRAISAL_DECIDE = "hr_eis.appraisal.decide"
P_LTC_APPLY = "hr_eis.ltc.apply"
P_LTC_VIEW_SELF = "hr_eis.ltc.view_self"
P_LTC_VIEW = "hr_eis.ltc.view"
P_LTC_VERIFY = "hr_eis.ltc.verify"
P_LTC_DECIDE = "hr_eis.ltc.decide"
P_LTC_PROCESS = "hr_eis.ltc.process"
P_CPDA_APPLY = "hr_eis.cpda.apply"
P_CPDA_VIEW_SELF = "hr_eis.cpda.view_self"
P_CPDA_VIEW = "hr_eis.cpda.view"
P_CPDA_VERIFY = "hr_eis.cpda.verify"
P_CPDA_DECIDE = "hr_eis.cpda.decide"
P_CPDA_PROCESS = "hr_eis.cpda.process"
P_NOTIFICATION_VIEW_SELF = "hr_eis.notification.view_self"
P_AUDIT_VIEW = "hr_eis.audit.view"
P_WORKFLOW_CONFIGURE = "hr_eis.workflow.configure"


def _actor(request):
    return getattr(request, "principal", None)


def _is_employee(actor) -> bool:
    roles = getattr(actor, "roles", ()) or ()
    staff_roles = {"hr_administrator", "hod", "registrar", "director",
                   "accountant"}
    return not any(r in staff_roles for r in roles)


def _own_only_or_403(actor, target_user_id: int):
    if _is_employee(actor) and int(target_user_id) != int(actor.user_id):
        raise PermissionDeniedError("Employees may view only their own records.",
                                    code="own_record_only")


# --------------------------------------------------------------------------- #
# service records
# --------------------------------------------------------------------------- #
class ServiceRecordView(APIView):
    permission_classes = [MODULE,
                          HasPermission(P_SERVICE_RECORD_VIEW)]

    def get(self, request):
        actor = _actor(request)
        target = request.query_params.get("user_id")
        user_id = int(target) if target else actor.user_id
        _own_only_or_403(actor, user_id)
        record = contracts.service_record_for(user_id)
        if record is None:
            raise NotFoundError("No service record for this employee.",
                                code="no_service_record")
        return Response(s.ServiceRecordSerializer(record).data)


class ServiceRecordManageView(APIView):
    permission_classes = [MODULE,
                          HasPermission(P_SERVICE_RECORD_MANAGE)]

    def post(self, request):
        actor = _actor(request)
        payload = s.ServiceRecordWriteSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        data = dict(payload.validated_data)
        user_id = int(data.pop("user_id"))
        record = services.create_service_record(actor, user_id=user_id, **data)
        return Response(s.ServiceRecordSerializer(record).data,
                        status=status.HTTP_201_CREATED)

    def put(self, request, user_id):
        actor = _actor(request)
        payload = s.ServiceRecordWriteSerializer(data=request.data, partial=True)
        payload.is_valid(raise_exception=True)
        record = services.update_service_record(actor, user_id,
                                                **payload.validated_data)
        return Response(s.ServiceRecordSerializer(record).data)


# --------------------------------------------------------------------------- #
# leave
# --------------------------------------------------------------------------- #
class LeaveRequestListCreateView(generics.ListCreateAPIView):
    serializer_class = s.LeaveRequestSerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [MODULE, HasPermission(P_LEAVE_APPLY)]
        return [MODULE,
                HasPermission(P_LEAVE_VIEW_SELF, P_LEAVE_VIEW)]

    def get_queryset(self):
        actor = _actor(self.request)
        return selectors.leave_requests_for(
            actor, mine_only=_is_employee(actor),
            status=self.request.query_params.get("status"),
            authority_role=self.request.query_params.get("authority_role"))

    def perform_create(self, serializer):
        actor = _actor(self.request)
        payload = s.LeaveRequestSubmitSerializer(data=self.request.data)
        payload.is_valid(raise_exception=True)
        d = payload.validated_data
        req = services.submit_leave_request(
            actor, leave_type=d["leave_type"], duration_days=d["duration_days"],
            justification=d["justification"])
        serializer.instance = req


class LeaveRequestDecideView(APIView):
    permission_classes = [MODULE, HasPermission(P_LEAVE_DECIDE)]

    def post(self, request, pk):
        actor = _actor(request)
        payload = s.LeaveRequestDecideSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        try:
            req = services.decide_leave_request(
                actor, request_id=int(pk), outcome=payload.validated_data["outcome"],
                remarks=payload.validated_data.get("remarks", ""))
        except services.NotFoundError as exc:
            raise NotFoundError(str(exc), code="no_leave_request") from exc
        return Response(s.LeaveRequestSerializer(req).data)


# --------------------------------------------------------------------------- #
# appraisal
# --------------------------------------------------------------------------- #
class AppraisalListCreateView(generics.ListCreateAPIView):
    serializer_class = s.AppraisalSerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [MODULE, HasPermission(P_APPRAISAL_SUBMIT)]
        return [MODULE,
                HasPermission(P_APPRAISAL_VIEW_SELF, P_APPRAISAL_VIEW)]

    def get_queryset(self):
        actor = _actor(self.request)
        return selectors.appraisals_for(
            actor, mine_only=_is_employee(actor),
            status=self.request.query_params.get("status"))

    def perform_create(self, serializer):
        actor = _actor(self.request)
        payload = s.AppraisalSubmitSerializer(data=self.request.data)
        payload.is_valid(raise_exception=True)
        appraisal = services.submit_appraisal(actor, year=payload.validated_data["year"])
        serializer.instance = appraisal


class AppraisalAssignReviewerView(APIView):
    permission_classes = [MODULE,
                          HasPermission(P_APPRAISAL_ASSIGN_REVIEWER)]

    def post(self, request, pk):
        actor = _actor(request)
        payload = s.AppraisalAssignSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        appraisal = services.assign_appraisal_reviewer(
            actor, appraisal_id=int(pk),
            reviewer_user_id=payload.validated_data["reviewer_user_id"])
        return Response(s.AppraisalSerializer(appraisal).data)


class AppraisalFinalizeView(APIView):
    permission_classes = [MODULE, HasPermission(P_APPRAISAL_DECIDE)]

    def post(self, request, pk):
        actor = _actor(request)
        appraisal = services.finalize_appraisal(actor, appraisal_id=int(pk))
        return Response(s.AppraisalSerializer(appraisal).data)


# --------------------------------------------------------------------------- #
# LTC
# --------------------------------------------------------------------------- #
class LTCRequestListCreateView(generics.ListCreateAPIView):
    serializer_class = s.LTCRequestSerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [MODULE, HasPermission(P_LTC_APPLY)]
        return [MODULE, HasPermission(P_LTC_VIEW_SELF, P_LTC_VIEW)]

    def get_queryset(self):
        actor = _actor(self.request)
        return selectors.financial_requests_for(
            m.LTCRequest, actor, mine_only=_is_employee(actor),
            status=self.request.query_params.get("status"),
            authority_role=self.request.query_params.get("authority_role"))

    def perform_create(self, serializer):
        actor = _actor(self.request)
        payload = s.LTCSubmitSerializer(data=self.request.data)
        payload.is_valid(raise_exception=True)
        d = payload.validated_data
        req = services.submit_ltc_request(
            actor, request_type=d["request_type"], amount=d["amount"],
            purpose=d.get("purpose", ""), documents=d.get("documents"))
        serializer.instance = req


class LTCRequestVerifyView(APIView):
    permission_classes = [MODULE, HasPermission(P_LTC_VERIFY)]

    def post(self, request, pk):
        actor = _actor(request)
        payload = s.LTCVerifySerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        req = services.verify_ltc_request(
            actor, request_id=int(pk), verified=payload.validated_data["verified"],
            notes=payload.validated_data.get("notes", ""))
        return Response(s.LTCRequestSerializer(req).data)


class LTCRequestDecideView(APIView):
    permission_classes = [MODULE, HasPermission(P_LTC_DECIDE)]

    def post(self, request, pk):
        actor = _actor(request)
        payload = s.LTCDecideSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        req = services.decide_ltc_request(
            actor, request_id=int(pk), outcome=payload.validated_data["outcome"],
            remarks=payload.validated_data.get("remarks", ""))
        return Response(s.LTCRequestSerializer(req).data)


class LTCRequestProcessView(APIView):
    permission_classes = [MODULE, HasPermission(P_LTC_PROCESS)]

    def post(self, request, pk):
        actor = _actor(request)
        payload = s.LTCProcessSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        req = services.process_ltc_claim(
            actor, request_id=int(pk),
            payment_status=payload.validated_data.get("payment_status", ""),
            disbursement_status=payload.validated_data.get(
                "disbursement_status", ""))
        return Response(s.LTCRequestSerializer(req).data)


# --------------------------------------------------------------------------- #
# CPDA
# --------------------------------------------------------------------------- #
class CPDARequestListCreateView(generics.ListCreateAPIView):
    serializer_class = s.CPDARequestSerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [MODULE, HasPermission(P_CPDA_APPLY)]
        return [MODULE, HasPermission(P_CPDA_VIEW_SELF, P_CPDA_VIEW)]

    def get_queryset(self):
        actor = _actor(self.request)
        return selectors.financial_requests_for(
            m.CPDARequest, actor, mine_only=_is_employee(actor),
            status=self.request.query_params.get("status"),
            authority_role=self.request.query_params.get("authority_role"))

    def perform_create(self, serializer):
        actor = _actor(self.request)
        payload = s.CPDASubmitSerializer(data=self.request.data)
        payload.is_valid(raise_exception=True)
        d = payload.validated_data
        req = services.submit_cpda_request(
            actor, purpose=d["purpose"], amount=d["amount"],
            documents=d.get("documents"))
        serializer.instance = req


class CPDARequestVerifyView(APIView):
    permission_classes = [MODULE, HasPermission(P_CPDA_VERIFY)]

    def post(self, request, pk):
        actor = _actor(request)
        payload = s.CPDAVerifySerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        req = services.verify_cpda_request(
            actor, request_id=int(pk), verified=payload.validated_data["verified"],
            notes=payload.validated_data.get("notes", ""))
        return Response(s.CPDARequestSerializer(req).data)


class CPDARequestDecideView(APIView):
    permission_classes = [MODULE, HasPermission(P_CPDA_DECIDE)]

    def post(self, request, pk):
        actor = _actor(request)
        payload = s.CPDADecideSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        req = services.decide_cpda_request(
            actor, request_id=int(pk), outcome=payload.validated_data["outcome"],
            remarks=payload.validated_data.get("remarks", ""))
        return Response(s.CPDARequestSerializer(req).data)


class CPDARequestProcessView(APIView):
    permission_classes = [MODULE, HasPermission(P_CPDA_PROCESS)]

    def post(self, request, pk):
        actor = _actor(request)
        payload = s.CPDAProcessSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        req = services.process_cpda_claim(
            actor, request_id=int(pk),
            disbursement_status=payload.validated_data.get(
                "disbursement_status", ""))
        return Response(s.CPDARequestSerializer(req).data)


# --------------------------------------------------------------------------- #
# notifications / audit / workflow config
# --------------------------------------------------------------------------- #
class NotificationListView(generics.ListAPIView):
    serializer_class = s.NotificationSerializer
    permission_classes = [MODULE, HasPermission(P_NOTIFICATION_VIEW_SELF)]

    def get_queryset(self):
        actor = _actor(self.request)
        return selectors.notifications_for(actor.user_id,
                                           unread_only=bool(
                                               self.request.query_params.get(
                                                   "unread_only")))


class AuditLogListView(generics.ListAPIView):
    serializer_class = s.AuditLogSerializer
    permission_classes = [MODULE, HasPermission(P_AUDIT_VIEW)]

    def get_queryset(self):
        return selectors.audit_logs_for(
            limit=int(self.request.query_params.get("limit", 100)))


class WorkflowConfigView(APIView):
    permission_classes = [MODULE, HasPermission(P_WORKFLOW_CONFIGURE)]

    def get(self, request):
        rows = m.WorkflowConfig.objects.all().order_by("key")
        return Response(s.WorkflowConfigSerializer(rows, many=True).data)

    def post(self, request):
        actor = _actor(request)
        payload = s.WorkflowConfigWriteSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        d = payload.validated_data
        obj, _ = m.WorkflowConfig.objects.update_or_create(
            key=d["key"],
            defaults={"value": d["value"],
                      "description": d.get("description", "")})
        services.record_audit(actor, "workflow_config.updated",
                              "workflow_config", None, {"key": d["key"]})
        return Response(s.WorkflowConfigSerializer(obj).data,
                        status=status.HTTP_201_CREATED)
