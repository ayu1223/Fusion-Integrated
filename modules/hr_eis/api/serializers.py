"""HR-EIS API serializers. Explicit allow-lists only."""
from rest_framework import serializers

from modules.hr_eis import models as m


class ServiceRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = m.EmployeeServiceRecord
        fields = (
            "user_id", "employee_id", "category", "department", "designation",
            "appointment_details", "service_history", "leave_balances",
            "retirement_status", "is_active", "created_at", "updated_at",
        )
        read_only_fields = fields


class ServiceRecordWriteSerializer(serializers.Serializer):
    category = serializers.ChoiceField(
        choices=m.EmployeeServiceRecord.CATEGORY)
    employee_id = serializers.CharField(max_length=40, required=False,
                                        allow_blank=True)
    department = serializers.CharField(max_length=80, required=False,
                                       allow_blank=True)
    designation = serializers.CharField(max_length=80, required=False,
                                        allow_blank=True)
    appointment_details = serializers.CharField(required=False, allow_blank=True)
    service_history = serializers.CharField(required=False, allow_blank=True)
    leave_balances = serializers.DictField(required=False, default=dict)
    retirement_status = serializers.ChoiceField(
        choices=m.EmployeeServiceRecord.RETIREMENT, required=False)
    is_active = serializers.BooleanField(required=False)


class LeaveRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = m.LeaveRequest
        fields = (
            "id", "user_id", "leave_type", "duration_days", "justification",
            "status", "current_authority_role", "decided_by_user_id",
            "decided_at", "remarks", "created_at", "updated_at",
        )
        read_only_fields = fields


class LeaveRequestSubmitSerializer(serializers.Serializer):
    leave_type = serializers.ChoiceField(choices=m.LeaveRequest.TYPE)
    duration_days = serializers.IntegerField(min_value=1)
    justification = serializers.CharField(allow_blank=False)


class LeaveRequestDecideSerializer(serializers.Serializer):
    outcome = serializers.ChoiceField(choices=("approved", "rejected",
                                               "forwarded"))
    remarks = serializers.CharField(required=False, allow_blank=True)


class AppraisalSerializer(serializers.ModelSerializer):
    class Meta:
        model = m.Appraisal
        fields = (
            "id", "user_id", "year", "status", "reviewer_user_id",
            "submitted_at", "finalized_at", "created_at", "updated_at",
        )
        read_only_fields = fields


class AppraisalSubmitSerializer(serializers.Serializer):
    year = serializers.IntegerField(min_value=1900, max_value=2100)


class AppraisalAssignSerializer(serializers.Serializer):
    reviewer_user_id = serializers.IntegerField()


class LTCRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = m.LTCRequest
        fields = (
            "id", "user_id", "request_type", "amount", "purpose", "documents",
            "status", "current_authority_role", "verified_by_user_id",
            "verified_at", "verification_notes", "decided_by_user_id",
            "decided_at", "remarks", "payment_status", "disbursement_status",
            "processed_by_user_id", "processed_at", "created_at", "updated_at",
        )
        read_only_fields = fields


class LTCSubmitSerializer(serializers.Serializer):
    request_type = serializers.ChoiceField(choices=m.LTCRequest.TYPE)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2,
                                      min_value=0)
    purpose = serializers.CharField(required=False, allow_blank=True)
    documents = serializers.ListField(required=False, default=list)


class LTCVerifySerializer(serializers.Serializer):
    verified = serializers.BooleanField()
    notes = serializers.CharField(required=False, allow_blank=True)


class LTCDecideSerializer(serializers.Serializer):
    outcome = serializers.ChoiceField(choices=("approved", "rejected",
                                               "forwarded"))
    remarks = serializers.CharField(required=False, allow_blank=True)


class LTCProcessSerializer(serializers.Serializer):
    payment_status = serializers.CharField(required=False, allow_blank=True)
    disbursement_status = serializers.CharField(required=False,
                                                allow_blank=True)


class CPDARequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = m.CPDARequest
        fields = (
            "id", "user_id", "request_type", "purpose", "amount", "documents",
            "status", "current_authority_role", "verified_by_user_id",
            "verified_at", "verification_notes", "decided_by_user_id",
            "decided_at", "remarks", "disbursement_status",
            "processed_by_user_id", "processed_at", "created_at", "updated_at",
        )
        read_only_fields = fields


class CPDASubmitSerializer(serializers.Serializer):
    purpose = serializers.CharField(allow_blank=False)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2,
                                      min_value=0)
    documents = serializers.ListField()


class CPDAVerifySerializer(serializers.Serializer):
    verified = serializers.BooleanField()
    notes = serializers.CharField(required=False, allow_blank=True)


class CPDADecideSerializer(serializers.Serializer):
    outcome = serializers.ChoiceField(choices=("approved", "rejected",
                                               "forwarded"))
    remarks = serializers.CharField(required=False, allow_blank=True)


class CPDAProcessSerializer(serializers.Serializer):
    disbursement_status = serializers.CharField(required=False,
                                                allow_blank=True)


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = m.HRNotification
        fields = (
            "id", "recipient_user_id", "type", "subject", "message", "channel",
            "status", "read_at", "request_type", "request_id", "created_at",
        )
        read_only_fields = fields


class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = m.AuditLog
        fields = (
            "id", "actor_user_id", "actor_label", "action", "entity_type",
            "entity_id", "details", "created_at",
        )
        read_only_fields = fields


class WorkflowConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = m.WorkflowConfig
        fields = ("key", "value", "description")


class WorkflowConfigWriteSerializer(serializers.Serializer):
    key = serializers.CharField(max_length=80)
    value = serializers.JSONField(default=dict)
    description = serializers.CharField(required=False, allow_blank=True)
