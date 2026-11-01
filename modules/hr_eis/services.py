"""HR-EIS domain services: validation, routing, state transitions, audit.

Every public function runs in a single transaction and writes an audit row, so
a request and its trace commit together or not at all (HR-AFR-102/103).
"""
from __future__ import annotations

from django.db import transaction
from django.utils import timezone

from core.api.exceptions import (
    BadRequestError, ConflictError, DomainError, NotFoundError,
    PermissionDeniedError,
)
from modules.hr_eis import models as m

LEAVE_TYPES = {c[0] for c in m.LeaveRequest.TYPE}
FINANCIAL_TYPES = {c[0] for c in m.LTCRequest.TYPE}
APPROVING_ROLES = ("hod", "registrar", "director")


class InsufficientBalanceError(DomainError):
    code = "insufficient_balance"
    status_code = 409
    message = "Leave balance is insufficient for the requested duration."


class WorkflowBypassError(DomainError):
    code = "workflow_bypass"
    status_code = 403
    message = "You are not the current authority for this request."


class WindowClosedError(DomainError):
    code = "window_closed"
    status_code = 409
    message = "The configured submission window is not open."


# --------------------------------------------------------------------------- #
# routing
# --------------------------------------------------------------------------- #

def _config_value(key: str, default=None):
    row = m.WorkflowConfig.objects.filter(key=key).first()
    return row.value if row is not None else default


def authority_for(request_type: str, employee_category: str) -> str:
    """The configured approval authority for a request type + category.

    Falls back to institutional defaults: faculty -> director, staff -> hod.
    HR-EIS never invents an authority; configuration is read-only here.
    (HR-AFR-006/007/008/009)
    """
    configured = _config_value(f"workflow.{request_type}.{employee_category}")
    if isinstance(configured, dict) and configured.get("authority_role"):
        return configured["authority_role"]
    if employee_category == "faculty":
        return "director"
    return "hod"


def next_authority(request_type: str, employee_category: str,
                   current: str) -> str | None:
    """The next configured authority after `current`, or None if this is final."""
    chain = _config_value(f"workflow.chain.{request_type}.{employee_category}")
    if isinstance(chain, list):
        try:
            idx = chain.index(current)
        except ValueError:
            return None
        return chain[idx + 1] if idx + 1 < len(chain) else None
    # Single authority: nothing is forwarded onward.
    return None


# --------------------------------------------------------------------------- #
# cross-cutting
# --------------------------------------------------------------------------- #

def record_audit(actor, action: str, entity_type: str, entity_id=None,
                 details=None) -> m.AuditLog:
    return m.AuditLog.objects.create(
        actor_user_id=actor.user_id,
        actor_label=getattr(actor, "display_name", "") or str(actor.user_id),
        action=action, entity_type=entity_type, entity_id=entity_id,
        details=details or {})


def _is_authority(actor, role: str) -> bool:
    return bool(getattr(actor, "roles", ())) and role in actor.roles


def notify(recipient_user_id: int, n_type: str, subject: str, message: str,
           channel: str = "both", request_type: str = "",
           request_id=None) -> m.HRNotification:
    """Generate a system notification. Delivery (dashboard/email) is handled
    by Fusion's delivery infrastructure; HR-EIS records and exposes it.
    (HR-AFR-077..082)
    """
    return m.HRNotification.objects.create(
        recipient_user_id=recipient_user_id, type=n_type, subject=subject,
        message=message, channel=channel, request_type=request_type,
        request_id=request_id)


def service_record_for(actor, user_id: int) -> m.EmployeeServiceRecord:
    try:
        return m.EmployeeServiceRecord.objects.get(pk=int(user_id))
    except m.EmployeeServiceRecord.DoesNotExist as exc:
        raise NotFoundError("No service record exists for this employee.",
                            code="no_service_record") from exc


# --------------------------------------------------------------------------- #
# service records  (HR-AFR-003, 019..028)
# --------------------------------------------------------------------------- #

@transaction.atomic
def create_service_record(actor, user_id: int, category: str,
                          department: str = "", designation: str = "",
                          employee_id: str = "", appointment_details: str = "",
                          service_history: str = "",
                          leave_balances=None,
                          retirement_status: str = "active",
                          is_active: bool = True) -> m.EmployeeServiceRecord:
    """HR Administrator creates an official service record."""
    if m.EmployeeServiceRecord.objects.filter(pk=user_id).exists():
        raise ConflictError("A service record already exists for this employee.",
                            code="service_record_exists")
    record = m.EmployeeServiceRecord.objects.create(
        user_id=user_id, category=category, department=department,
        designation=designation, employee_id=employee_id,
        appointment_details=appointment_details, service_history=service_history,
        leave_balances=leave_balances or {},
        retirement_status=retirement_status, is_active=is_active)
    record_audit(actor, "service_record.created", "service_record", record.user_id,
                 {"category": category})
    return record


@transaction.atomic
def update_service_record(actor, user_id: int, **fields) -> m.EmployeeServiceRecord:
    """HR Administrator updates a service record consistently (all-or-nothing)."""
    record = service_record_for(actor, user_id)
    allowed = {
        "category", "department", "designation", "employee_id",
        "appointment_details", "service_history", "leave_balances",
        "retirement_status", "is_active",
    }
    dirty = {k: v for k, v in fields.items() if k in allowed and v is not None}
    if not dirty:
        return record
    for k, v in dirty.items():
        setattr(record, k, v)
    record.save()
    record_audit(actor, "service_record.updated", "service_record", record.user_id,
                 {"fields": sorted(dirty)})
    return record


# --------------------------------------------------------------------------- #
# leave  (HR-AFR-029..043)
# --------------------------------------------------------------------------- #

@transaction.atomic
def submit_leave_request(actor, leave_type: str, duration_days: int,
                         justification: str) -> m.LeaveRequest:
    """Employee submits a leave request; balance + eligibility validated first."""
    if leave_type not in LEAVE_TYPES:
        raise BadRequestError(f"Unsupported leave type '{leave_type}'.",
                              code="invalid_leave_type")
    if not duration_days or duration_days <= 0:
        raise BadRequestError("duration_days must be a positive integer.",
                              code="invalid_duration")
    if not justification or not justification.strip():
        raise BadRequestError("justification is required.",
                              code="justification_required")

    record = service_record_for(actor, actor.user_id)
    if record.retirement_status == "retired":
        raise ConflictError("Retired employees cannot apply for leave.",
                            code="retired_employee")

    balance = int(record.leave_balances.get(leave_type, 0) or 0)
    if duration_days > balance:
        raise InsufficientBalanceError(
            f"Only {balance} {leave_type} leave day(s) remaining.",
            details={"balance": balance, "requested": duration_days})

    req = m.LeaveRequest.objects.create(
        user_id=actor.user_id, leave_type=leave_type, duration_days=duration_days,
        justification=justification.strip(), status="submitted")
    role = authority_for("leave", record.category)
    req.current_authority_role = role
    req.status = "pending"
    req.save()
    record_audit(actor, "leave_request.submitted", "leave_request", req.pk,
                 {"leave_type": leave_type, "duration_days": duration_days,
                  "authority_role": role})
    notify(actor.user_id, "submission", "Leave request submitted",
           f"Your {leave_type} leave request ({duration_days} day(s)) has been "
           f"submitted and routed to {role}.", request_type="leave",
           request_id=req.pk)
    return req


@transaction.atomic
def decide_leave_request(actor, request_id: int, outcome: str,
                         remarks: str = "") -> m.LeaveRequest:
    """Approving authority approves / rejects / forwards a leave request."""
    if outcome not in ("approved", "rejected", "forwarded"):
        raise BadRequestError("Outcome must be approved, rejected or forwarded.",
                              code="invalid_outcome")
    if not _is_authority(actor, ""):
        pass  # role checked below against current_authority_role

    try:
        req = m.LeaveRequest.objects.select_for_update().get(pk=request_id)
    except m.LeaveRequest.DoesNotExist as exc:
        raise NotFoundError("No such leave request.", code="no_leave_request") from exc

    if req.status != "pending":
        raise ConflictError(
            f"This request is already {req.status}; workflow order cannot be "
            f"altered.", code="workflow_order_violation")
    if not _is_authority(actor, req.current_authority_role):
        raise WorkflowBypassError(
            f"{req.current_authority_role} is the current authority; your role "
            f"cannot decide this request.")

    if outcome == "approved":
        record = service_record_for(actor, req.user_id)
        balance = int(record.leave_balances.get(req.leave_type, 0) or 0)
        if balance < req.duration_days:
            raise ConflictError(
                "Leave balance is no longer sufficient.", code="balance_stale")
        record.leave_balances[req.leave_type] = balance - req.duration_days
        record.save(update_fields=["leave_balances", "updated_at"])
        req.status = "approved"
        record_audit(actor, "leave_request.approved", "leave_request", req.pk,
                     {"remarks": remarks})
        notify(req.user_id, "decision", "Leave request approved",
               f"Your {req.leave_type} leave request has been approved. Balance "
               f"updated to {record.leave_balances.get(req.leave_type, 0)} day(s).",
               request_type="leave", request_id=req.pk)
    elif outcome == "rejected":
        req.status = "rejected"
        record_audit(actor, "leave_request.rejected", "leave_request", req.pk,
                     {"remarks": remarks})
        notify(req.user_id, "decision", "Leave request rejected",
               f"Your {req.leave_type} leave request has been rejected.",
               request_type="leave", request_id=req.pk)
    else:  # forwarded
        nxt = next_authority("leave", service_record_for(actor, req.user_id).category,
                             req.current_authority_role)
        if nxt is None:
            raise ConflictError(
                "No next authority configured; this request cannot be forwarded.",
                code="no_next_authority")
        req.current_authority_role = nxt
        req.status = "pending"
        record_audit(actor, "leave_request.forwarded", "leave_request", req.pk,
                     {"from": req.current_authority_role, "to": nxt,
                      "remarks": remarks})
        notify(req.user_id, "decision", "Leave request forwarded",
               f"Your {req.leave_type} leave request has been forwarded to {nxt}.",
               request_type="leave", request_id=req.pk)

    req.decided_by_user_id = actor.user_id
    req.decided_at = timezone.now()
    req.remarks = remarks
    req.save(update_fields=["status", "current_authority_role",
                            "decided_by_user_id", "decided_at", "remarks",
                            "updated_at"])
    return req


# --------------------------------------------------------------------------- #
# appraisal  (HR-AFR-044..049)
# --------------------------------------------------------------------------- #

@transaction.atomic
def submit_appraisal(actor, year: int) -> m.Appraisal:
    """Employee submits a yearly appraisal within the configured window."""
    window = _config_value("appraisal.submission_window", {"open": True})
    if not window.get("open", True):
        raise WindowClosedError("Appraisal submissions are not open.",
                                code="appraisal_window_closed")
    if m.Appraisal.objects.filter(user_id=actor.user_id, year=year).exists():
        raise ConflictError("An appraisal already exists for this year.",
                            code="appraisal_exists")
    appraisal = m.Appraisal.objects.create(
        user_id=actor.user_id, year=year, status="submitted",
        submitted_at=timezone.now())
    record_audit(actor, "appraisal.submitted", "appraisal", appraisal.pk,
                 {"year": year})
    notify(actor.user_id, "submission", "Appraisal submitted",
           f"Your {year} yearly appraisal has been submitted.",
           request_type="appraisal", request_id=appraisal.pk)
    return appraisal


@transaction.atomic
def assign_appraisal_reviewer(actor, appraisal_id: int,
                              reviewer_user_id: int) -> m.Appraisal:
    """HR Administrator assigns a reviewer to a submitted appraisal."""
    try:
        appraisal = m.Appraisal.objects.select_for_update().get(pk=appraisal_id)
    except m.Appraisal.DoesNotExist as exc:
        raise NotFoundError("No such appraisal.", code="no_appraisal") from exc
    if appraisal.status != "submitted":
        raise ConflictError(
            f"Reviewers can only be assigned to a submitted appraisal "
            f"(current: {appraisal.status}).", code="invalid_appraisal_state")
    appraisal.reviewer_user_id = int(reviewer_user_id)
    appraisal.status = "reviewer_assigned"
    appraisal.save(update_fields=["reviewer_user_id", "status", "updated_at"])
    record_audit(actor, "appraisal.reviewer_assigned", "appraisal", appraisal.pk,
                 {"reviewer_user_id": reviewer_user_id})
    notify(appraisal.user_id, "decision", "Appraisal reviewer assigned",
           f"An appraisal reviewer has been assigned for {appraisal.year}.",
           request_type="appraisal", request_id=appraisal.pk)
    return appraisal


@transaction.atomic
def finalize_appraisal(actor, appraisal_id: int) -> m.Appraisal:
    """Designated appraisal authority finalizes and archives an appraisal."""
    try:
        appraisal = m.Appraisal.objects.select_for_update().get(pk=appraisal_id)
    except m.Appraisal.DoesNotExist as exc:
        raise NotFoundError("No such appraisal.", code="no_appraisal") from exc
    if appraisal.status == "closed":
        raise ConflictError("A closed appraisal cannot be modified.",
                            code="appraisal_closed")
    if not _is_authority(actor, ""):
        pass
    if appraisal.status not in ("reviewer_assigned", "pending_review"):
        raise ConflictError(
            f"Appraisal must be under review to finalize (current: "
            f"{appraisal.status}).", code="invalid_appraisal_state")
    appraisal.status = "finalized"
    appraisal.finalized_at = timezone.now()
    appraisal.save(update_fields=["status", "finalized_at", "updated_at"])
    record_audit(actor, "appraisal.finalized", "appraisal", appraisal.pk,
                 {"year": appraisal.year})
    notify(appraisal.user_id, "decision", "Appraisal finalized",
           f"Your {appraisal.year} appraisal has been finalized and archived.",
           request_type="appraisal", request_id=appraisal.pk)
    return appraisal


# --------------------------------------------------------------------------- #
# LTC  (HR-AFR-050..059)
# --------------------------------------------------------------------------- #

@transaction.atomic
def submit_ltc_request(actor, request_type: str, amount, purpose: str = "",
                       documents=None) -> m.LTCRequest:
    if request_type not in FINANCIAL_TYPES:
        raise BadRequestError("Unsupported LTC request type.",
                              code="invalid_ltc_type")
    amount = _decimal(amount)
    if amount <= 0:
        raise BadRequestError("amount must be positive.", code="invalid_amount")
    req = m.LTCRequest.objects.create(
        user_id=actor.user_id, request_type=request_type, amount=amount,
        purpose=purpose or "", documents=documents or [],
        status="awaiting_verification")
    record_audit(actor, "ltc_request.submitted", "ltc_request", req.pk,
                 {"request_type": request_type, "amount": str(amount)})
    notify(actor.user_id, "submission", "LTC request submitted",
           f"Your LTC {request_type} request (₹{amount}) is awaiting HR "
           f"verification.", request_type="ltc", request_id=req.pk)
    return req


@transaction.atomic
def verify_ltc_request(actor, request_id: int, verified: bool,
                       notes: str = "") -> m.LTCRequest:
    """HR Administrator verifies documentation + eligibility before routing."""
    try:
        req = m.LTCRequest.objects.select_for_update().get(pk=request_id)
    except m.LTCRequest.DoesNotExist as exc:
        raise NotFoundError("No such LTC request.", code="no_ltc_request") from exc
    if req.status != "awaiting_verification":
        raise ConflictError(
            f"Only an awaiting-verification LTC request can be verified "
            f"(current: {req.status}).", code="invalid_ltc_state")
    req.verified_by_user_id = actor.user_id
    req.verified_at = timezone.now()
    req.verification_notes = notes or ""
    if verified:
        record = service_record_for(actor, req.user_id)
        role = authority_for("ltc", record.category)
        req.current_authority_role = role
        req.status = "pending"
    record_audit(actor, "ltc_request.verified", "ltc_request", req.pk,
                 {"verified": verified, "notes": notes})
    if verified:
        notify(req.user_id, "decision", "LTC request verified",
               f"Your LTC {req.request_type} request has been verified and "
               f"routed to {role}.", request_type="ltc", request_id=req.pk)
    else:
        notify(req.user_id, "decision", "LTC verification not confirmed",
               f"Your LTC {req.request_type} request could not be verified and "
               f"remains outside approval routing.", request_type="ltc",
               request_id=req.pk)
    req.save(update_fields=["verified_by_user_id", "verified_at",
                            "verification_notes", "current_authority_role",
                            "status", "updated_at"])
    return req


@transaction.atomic
def decide_ltc_request(actor, request_id: int, outcome: str,
                       remarks: str = "") -> m.LTCRequest:
    return _decide_financial(actor, m.LTCRequest, "ltc", request_id, outcome,
                             remarks)


@transaction.atomic
def process_ltc_claim(actor, request_id: int, payment_status: str = "",
                      disbursement_status: str = "") -> m.LTCRequest:
    """Accountant records HR-EIS-side financial processing for an approved LTC
    claim. External payroll/finance execution stays outside HR-EIS.
    (HR-AFR-015/016/017/018, HR-AFR-104/105)
    """
    return _process_claim(actor, m.LTCRequest, "ltc", request_id,
                          payment_status, disbursement_status)


# --------------------------------------------------------------------------- #
# CPDA  (HR-AFR-060..069)
# --------------------------------------------------------------------------- #

@transaction.atomic
def submit_cpda_request(actor, purpose: str, amount, documents=None
                        ) -> m.CPDARequest:
    if not purpose or not purpose.strip():
        raise BadRequestError("purpose is required.", code="purpose_required")
    amount = _decimal(amount)
    if amount <= 0:
        raise BadRequestError("amount must be positive.", code="invalid_amount")
    if not documents:
        raise BadRequestError("supporting documents are required.",
                              code="documents_required")
    req = m.CPDARequest.objects.create(
        user_id=actor.user_id, request_type="advance", purpose=purpose.strip(),
        amount=amount, documents=list(documents), status="awaiting_verification")
    record_audit(actor, "cpda_request.submitted", "cpda_request", req.pk,
                 {"purpose": purpose, "amount": str(amount)})
    notify(actor.user_id, "submission", "CPDA request submitted",
           f"Your CPDA request (₹{amount}) is awaiting HR verification.",
           request_type="cpda", request_id=req.pk)
    return req


@transaction.atomic
def verify_cpda_request(actor, request_id: int, verified: bool,
                        notes: str = "") -> m.CPDARequest:
    try:
        req = m.CPDARequest.objects.select_for_update().get(pk=request_id)
    except m.CPDARequest.DoesNotExist as exc:
        raise NotFoundError("No such CPDA request.", code="no_cpda_request") from exc
    if req.status != "awaiting_verification":
        raise ConflictError(
            f"Only an awaiting-verification CPDA request can be verified "
            f"(current: {req.status}).", code="invalid_cpda_state")
    req.verified_by_user_id = actor.user_id
    req.verified_at = timezone.now()
    req.verification_notes = notes or ""
    if verified:
        record = service_record_for(actor, req.user_id)
        role = authority_for("cpda", record.category)
        req.current_authority_role = role
        req.status = "pending"
    record_audit(actor, "cpda_request.verified", "cpda_request", req.pk,
                 {"verified": verified, "notes": notes})
    if verified:
        notify(req.user_id, "decision", "CPDA request verified",
               f"Your CPDA request has been verified and routed to {role}.",
               request_type="cpda", request_id=req.pk)
    else:
        notify(req.user_id, "decision", "CPDA verification not confirmed",
               f"Your CPDA request could not be verified and remains outside "
               f"approval routing.", request_type="cpda", request_id=req.pk)
    req.save(update_fields=["verified_by_user_id", "verified_at",
                            "verification_notes", "current_authority_role",
                            "status", "updated_at"])
    return req


@transaction.atomic
def decide_cpda_request(actor, request_id: int, outcome: str,
                        remarks: str = "") -> m.CPDARequest:
    return _decide_financial(actor, m.CPDARequest, "cpda", request_id, outcome,
                             remarks)


@transaction.atomic
def process_cpda_claim(actor, request_id: int,
                       disbursement_status: str = "") -> m.CPDARequest:
    """Accountant records HR-EIS-side processing + disbursement details."""
    return _process_claim(actor, m.CPDARequest, "cpda", request_id,
                          "", disbursement_status)


# --------------------------------------------------------------------------- #
# shared financial-claim helpers
# --------------------------------------------------------------------------- #

def _decimal(value) -> float:
    from decimal import Decimal, InvalidOperation
    try:
        return float(Decimal(str(value)))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise BadRequestError("amount must be a number.", code="invalid_amount") from exc


def _decide_financial(actor, model, domain: str, request_id: int, outcome: str,
                      remarks: str):
    if outcome not in ("approved", "rejected", "forwarded"):
        raise BadRequestError("Outcome must be approved, rejected or forwarded.",
                              code="invalid_outcome")
    try:
        req = model.objects.select_for_update().get(pk=request_id)
    except model.DoesNotExist as exc:
        raise NotFoundError("No such request.", code=f"no_{domain}_request") from exc
    if req.status != "pending":
        raise ConflictError(
            f"This request is already {req.status}; workflow order cannot be "
            f"altered.", code="workflow_order_violation")
    if not _is_authority(actor, req.current_authority_role):
        raise WorkflowBypassError(
            f"{req.current_authority_role} is the current authority; your role "
            f"cannot decide this request.")

    record = service_record_for(actor, req.user_id)
    if outcome == "approved":
        req.status = "approved"
        record_audit(actor, f"{domain}_request.approved", domain, req.pk,
                     {"remarks": remarks})
        notify(req.user_id, "decision", f"{domain.upper()} request approved",
               f"Your {domain} {req.request_type} request has been approved.",
               request_type=domain, request_id=req.pk)
    elif outcome == "rejected":
        req.status = "rejected"
        record_audit(actor, f"{domain}_request.rejected", domain, req.pk,
                     {"remarks": remarks})
        notify(req.user_id, "decision", f"{domain.upper()} request rejected",
               f"Your {domain} {req.request_type} request has been rejected.",
               request_type=domain, request_id=req.pk)
    else:
        nxt = next_authority(domain, record.category,
                             req.current_authority_role)
        if nxt is None:
            raise ConflictError(
                "No next authority configured; this request cannot be forwarded.",
                code="no_next_authority")
        req.current_authority_role = nxt
        req.status = "pending"
        record_audit(actor, f"{domain}_request.forwarded", domain, req.pk,
                     {"to": nxt, "remarks": remarks})
        notify(req.user_id, "decision", f"{domain.upper()} request forwarded",
               f"Your {domain} {req.request_type} request has been forwarded to "
               f"{nxt}.", request_type=domain, request_id=req.pk)

    req.decided_by_user_id = actor.user_id
    req.decided_at = timezone.now()
    req.remarks = remarks
    req.save(update_fields=["status", "current_authority_role",
                            "decided_by_user_id", "decided_at", "remarks",
                            "updated_at"])
    return req


def _process_claim(actor, model, domain: str, request_id: int,
                   payment_status: str, disbursement_status: str):
    try:
        req = model.objects.select_for_update().get(pk=request_id)
    except model.DoesNotExist as exc:
        raise NotFoundError("No such request.", code=f"no_{domain}_request") from exc
    if req.status != "approved":
        raise ConflictError(
            f"Only an approved {domain} claim can be processed "
            f"(current: {req.status}).", code="not_approved")
    if payment_status:
        req.payment_status = payment_status
    if disbursement_status:
        req.disbursement_status = disbursement_status
    req.status = "financial_processing"
    req.processed_by_user_id = actor.user_id
    req.processed_at = timezone.now()
    record_audit(actor, f"{domain}_request.processed", domain, req.pk,
                 {"payment_status": payment_status,
                  "disbursement_status": disbursement_status})
    notify(req.user_id, "decision", f"{domain.upper()} claim processed",
           f"Your {domain} {req.request_type} claim has been recorded for "
           f"financial settlement.",
           request_type=domain, request_id=req.pk)
    req.save(update_fields=["payment_status", "disbursement_status", "status",
                            "processed_by_user_id", "processed_at", "updated_at"])
    return req
