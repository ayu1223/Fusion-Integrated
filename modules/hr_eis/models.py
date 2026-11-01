"""HR-EIS domain tables.

Institute people are referenced by plain `user_id` integers — there is no user
table in this database, so no cross-module foreign keys.
"""
from django.db import models
from django.db.models import Q

from core.db.mixins import TimeStampedModel, UserScopedModel


class EmployeeServiceRecord(TimeStampedModel):
    """One authoritative service record per employee (HR-AFR-019..028)."""

    CATEGORY = [("faculty", "Faculty"), ("staff", "Staff")]
    RETIREMENT = [("active", "Active"), ("retired", "Retired")]

    user_id = models.IntegerField(primary_key=True)      # IAM user id
    employee_id = models.CharField(max_length=40, unique=True, blank=True)
    category = models.CharField(max_length=16, choices=CATEGORY, db_index=True)
    department = models.CharField(max_length=80, blank=True)
    designation = models.CharField(max_length=80, blank=True)
    appointment_details = models.TextField(blank=True)
    service_history = models.TextField(blank=True)
    # leave_type -> remaining days, e.g. {"casual": 8, "earned": 30}
    leave_balances = models.JSONField(default=dict, blank=True)
    retirement_status = models.CharField(
        max_length=16, choices=RETIREMENT, default="active")
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "hr_eis_service_record"
        indexes = [
            models.Index(fields=["category"], name="servicerecord_category_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.employee_id or self.user_id} ({self.get_category_display()})"


class LeaveRequest(TimeStampedModel, UserScopedModel):
    """Employee leave application routed through an approval hierarchy."""

    TYPE = [
        ("casual", "Casual"), ("restricted", "Restricted"),
        ("medical", "Medical"), ("earned", "Earned"),
        ("vacation", "Vacation"), ("sabbatical", "Sabbatical"),
    ]
    STATUS = [
        ("submitted", "Submitted"),
        ("pending", "Pending Current Authority"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
        ("forwarded", "Forwarded"),
    ]

    leave_type = models.CharField(max_length=16, choices=TYPE)
    duration_days = models.PositiveIntegerField(help_text="Leave duration in days.")
    justification = models.TextField()
    status = models.CharField(max_length=16, choices=STATUS, default="submitted")
    current_authority_role = models.CharField(max_length=40, blank=True)
    decided_by_user_id = models.IntegerField(null=True, blank=True)
    decided_at = models.DateTimeField(null=True, blank=True)
    remarks = models.TextField(blank=True)

    class Meta:
        db_table = "hr_eis_leave_request"
        indexes = [
            models.Index(fields=["user_id", "status"], name="leaverequest_user_idx"),
            models.Index(fields=["status", "current_authority_role"],
                         name="leaverequest_authority_idx"),
        ]

    def __str__(self) -> str:
        return f"leave#{self.pk} u{self.user_id} {self.leave_type} ({self.status})"


class Appraisal(TimeStampedModel, UserScopedModel):
    """Yearly appraisal form (HR-AFR-044..049)."""

    STATUS = [
        ("submitted", "Submitted"),
        ("reviewer_assigned", "Reviewer Assigned"),
        ("pending_review", "Pending Review"),
        ("finalized", "Finalized"),
        ("closed", "Closed"),
    ]

    year = models.PositiveSmallIntegerField(db_index=True)
    status = models.CharField(max_length=20, choices=STATUS, default="submitted")
    reviewer_user_id = models.IntegerField(null=True, blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    finalized_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "hr_eis_appraisal"
        constraints = [
            models.UniqueConstraint(
                fields=["user_id", "year"], name="appraisal_unique_per_year")
        ]
        indexes = [
            models.Index(fields=["user_id", "status"], name="appraisal_user_idx"),
        ]

    def __str__(self) -> str:
        return f"appraisal u{self.user_id} {self.year} ({self.status})"


def _financial_statuses():
    return [
        ("submitted", "Submitted"),
        ("awaiting_verification", "Awaiting HR Verification"),
        ("pending", "Pending Current Authority"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
        ("financial_processing", "Financial Processing Recorded"),
        ("settled", "Settled"),
    ]


class LTCRequest(TimeStampedModel, UserScopedModel):
    """Leave Travel Concession advance / reimbursement claim (HR-AFR-050..059)."""

    TYPE = [("advance", "Advance"), ("reimbursement", "Reimbursement")]
    STATUS = _financial_statuses()

    request_type = models.CharField(max_length=16, choices=TYPE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    purpose = models.CharField(max_length=255, blank=True)
    # [{"name": "...", "url": "..."}]
    documents = models.JSONField(default=list, blank=True)
    status = models.CharField(max_length=24, choices=STATUS, default="submitted")
    current_authority_role = models.CharField(max_length=40, blank=True)
    verified_by_user_id = models.IntegerField(null=True, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    verification_notes = models.TextField(blank=True)
    decided_by_user_id = models.IntegerField(null=True, blank=True)
    decided_at = models.DateTimeField(null=True, blank=True)
    remarks = models.TextField(blank=True)
    payment_status = models.CharField(max_length=40, blank=True)
    disbursement_status = models.CharField(max_length=40, blank=True)
    processed_by_user_id = models.IntegerField(null=True, blank=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "hr_eis_ltc_request"
        indexes = [
            models.Index(fields=["user_id", "status"], name="ltcrequest_user_idx"),
            models.Index(fields=["status", "current_authority_role"],
                         name="ltcrequest_authority_idx"),
        ]

    def __str__(self) -> str:
        return f"ltc#{self.pk} u{self.user_id} {self.request_type} ({self.status})"


class CPDARequest(TimeStampedModel, UserScopedModel):
    """Cumulative Professional Development Allowance claim (HR-AFR-060..069)."""

    TYPE = [("advance", "Advance"), ("reimbursement", "Reimbursement")]
    STATUS = _financial_statuses()

    request_type = models.CharField(max_length=16, choices=TYPE)
    purpose = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    documents = models.JSONField(default=list, blank=True)
    status = models.CharField(max_length=24, choices=STATUS, default="submitted")
    current_authority_role = models.CharField(max_length=40, blank=True)
    verified_by_user_id = models.IntegerField(null=True, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    verification_notes = models.TextField(blank=True)
    decided_by_user_id = models.IntegerField(null=True, blank=True)
    decided_at = models.DateTimeField(null=True, blank=True)
    remarks = models.TextField(blank=True)
    disbursement_status = models.CharField(max_length=40, blank=True)
    processed_by_user_id = models.IntegerField(null=True, blank=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "hr_eis_cpda_request"
        indexes = [
            models.Index(fields=["user_id", "status"], name="cpdarequest_user_idx"),
            models.Index(fields=["status", "current_authority_role"],
                         name="cpdarequest_authority_idx"),
        ]

    def __str__(self) -> str:
        return f"cpda#{self.pk} u{self.user_id} {self.request_type} ({self.status})"


class WorkflowConfig(TimeStampedModel):
    """Key/value HR-EIS workflow configuration set by the HR Administrator.

    Keys like `workflow.leave.<category>` name an authority role; keys like
    `workflow.chain.<request>.<category>` name an ordered authority list.
    (HR-AFR-012, HR-UC-017)
    """

    key = models.CharField(max_length=80, unique=True, db_index=True)
    value = models.JSONField(default=dict, blank=True)
    description = models.CharField(max_length=200, blank=True)

    class Meta:
        db_table = "hr_eis_workflow_config"

    def __str__(self) -> str:
        return self.key


class HRNotification(TimeStampedModel):
    """System notification exposed on the dashboard / email path (HR-AFR-077..082)."""

    TYPE = [
        ("submission", "Request submission"),
        ("decision", "Approval / rejection / forwarding"),
        ("reminder", "Pending-action reminder"),
        ("policy_update", "Policy / deadline update"),
    ]
    CHANNEL = [("dashboard", "Dashboard"), ("email", "Email"), ("both", "Both")]
    STATUS = [("pending", "Pending"), ("sent", "Sent"), ("read", "Read")]

    recipient_user_id = models.IntegerField(db_index=True)
    type = models.CharField(max_length=20, choices=TYPE)
    subject = models.CharField(max_length=200)
    message = models.TextField()
    channel = models.CharField(max_length=10, choices=CHANNEL, default="both")
    status = models.CharField(max_length=10, choices=STATUS, default="pending")
    read_at = models.DateTimeField(null=True, blank=True)
    request_type = models.CharField(max_length=20, blank=True)
    request_id = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = "hr_eis_notification"
        indexes = [
            models.Index(fields=["recipient_user_id", "-created_at"],
                         name="notification_recipient_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.get_type_display()} -> u{self.recipient_user_id}"


class AuditLog(TimeStampedModel):
    """Immutable HR transaction log: actor, timestamp, action (HR-AFR-083..089)."""

    actor_user_id = models.IntegerField(db_index=True)
    actor_label = models.CharField(max_length=120, blank=True)
    action = models.CharField(max_length=60, db_index=True)
    entity_type = models.CharField(max_length=40)
    entity_id = models.IntegerField(null=True, blank=True)
    details = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "hr_eis_audit_log"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["actor_user_id", "-created_at"],
                         name="auditlog_actor_idx"),
            models.Index(fields=["action", "-created_at"], name="auditlog_action_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.action} by u{self.actor_user_id} @ {self.created_at}"

    def save(self, *args, **kwargs):
        """Audit rows are append-only: an existing row may not be updated."""
        if self.pk is not None:
            self.__class__.objects.filter(pk=self.pk).exists()
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise NotImplementedError("Audit log entries are immutable.")
