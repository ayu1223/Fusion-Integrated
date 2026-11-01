"""HR-EIS public surface. Other modules import only from here."""
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from modules.hr_eis.models import EmployeeServiceRecord


@dataclass(frozen=True)
class ServiceRecordDTO:
    user_id: int
    employee_id: str
    category: str
    department: str
    designation: str
    appointment_details: str
    service_history: str
    leave_balances: dict
    retirement_status: str
    is_active: bool


def _to_dto(r: EmployeeServiceRecord) -> ServiceRecordDTO:
    return ServiceRecordDTO(
        user_id=r.user_id, employee_id=r.employee_id, category=r.category,
        department=r.department, designation=r.designation,
        appointment_details=r.appointment_details, service_history=r.service_history,
        leave_balances=r.leave_balances, retirement_status=r.retirement_status,
        is_active=r.is_active,
    )


def get_service_records(user_ids: Sequence[int]) -> dict[int, ServiceRecordDTO]:
    """Batched lookup; a missing id is simply absent from the mapping."""
    ids = {int(i) for i in user_ids if i is not None}
    if not ids:
        return {}
    return {
        r.user_id: _to_dto(r)
        for r in EmployeeServiceRecord.objects.filter(user_id__in=ids)
    }


def service_record_for(user_id: int) -> ServiceRecordDTO | None:
    try:
        r = EmployeeServiceRecord.objects.get(pk=int(user_id))
    except EmployeeServiceRecord.DoesNotExist:
        return None
    return _to_dto(r)
