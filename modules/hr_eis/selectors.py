"""Read-side queries for HR-EIS. Selectors decide what is visible; they never
authorise a write — that is the view/service's job."""
from __future__ import annotations

from django.db.models import Q

from modules.hr_eis import models as m


def leave_requests_for(actor, *, mine_only=False, status=None,
                       authority_role=None):
    qs = m.LeaveRequest.objects.all()
    if mine_only:
        qs = qs.filter(user_id=actor.user_id)
    if status:
        qs = qs.filter(status=status)
    if authority_role:
        qs = qs.filter(current_authority_role=authority_role)
    # Non-own rows are only visible to someone with an authority/admin role;
    # the view's permission gate already narrowed the actor, so here we just
    # order. Everything an actor may not see is filtered out at the gate.
    return qs.order_by("-created_at")


def appraisals_for(actor, *, mine_only=False, status=None):
    qs = m.Appraisal.objects.all()
    if mine_only:
        qs = qs.filter(user_id=actor.user_id)
    if status:
        qs = qs.filter(status=status)
    return qs.order_by("-created_at")


def financial_requests_for(model, actor, *, mine_only=False, status=None,
                           authority_role=None):
    qs = model.objects.all()
    if mine_only:
        qs = qs.filter(user_id=actor.user_id)
    if status:
        qs = qs.filter(status=status)
    if authority_role:
        qs = qs.filter(current_authority_role=authority_role)
    return qs.order_by("-created_at")


def notifications_for(recipient_user_id, *, unread_only=False, limit=50):
    qs = m.HRNotification.objects.filter(recipient_user_id=recipient_user_id)
    if unread_only:
        qs = qs.exclude(status="read")
    return qs.order_by("-created_at")[:limit]


def audit_logs_for(*, limit=100, actor_user_id=None, action=None):
    qs = m.AuditLog.objects.all()
    if actor_user_id is not None:
        qs = qs.filter(actor_user_id=actor_user_id)
    if action:
        qs = qs.filter(action=action)
    return qs[:limit]
