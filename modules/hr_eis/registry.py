"""HR-EIS module registry: nav, permissions, designation grants (ADR-0010)."""

MODULE = {
    "code": "hr_eis",
    "label": "HR — Employee Information System",
    "icon": "FaUser",
    "base_path": "/hr-eis",
    "nav_section": "HR",
    "sort_order": 20,
    "status": "active",
}

NAV_ITEMS = [
    # -- employee -----------------------------------------------------------
    {"code": "hr_eis.my_record", "label": "My Service Record",
     "icon": "FaIdCard", "to": "/hr-eis/my-record",
     "required_permission": "hr_eis.service_record.view", "sort_order": 5},
    {"code": "hr_eis.my_requests", "label": "My HR Requests",
     "icon": "FaClipboardList", "to": "/hr-eis/my-requests",
     "required_permission": "hr_eis.leave.view_self", "sort_order": 10},
    {"code": "hr_eis.apply_leave", "label": "Apply for Leave",
     "icon": "FaCalendarPlus", "to": "/hr-eis/apply-leave",
     "required_permission": "hr_eis.leave.apply", "sort_order": 15},
    {"code": "hr_eis.submit_appraisal", "label": "Yearly Appraisal",
     "icon": "FaFileAlt", "to": "/hr-eis/appraisal",
     "required_permission": "hr_eis.appraisal.submit", "sort_order": 20},
    {"code": "hr_eis.apply_ltc", "label": "LTC Claim",
     "icon": "FaPlane", "to": "/hr-eis/ltc",
     "required_permission": "hr_eis.ltc.apply", "sort_order": 25},
    {"code": "hr_eis.apply_cpda", "label": "CPDA Claim",
     "icon": "FaBook", "to": "/hr-eis/cpda",
     "required_permission": "hr_eis.cpda.apply", "sort_order": 30},
    {"code": "hr_eis.my_notifications", "label": "My Notifications",
     "icon": "FaBell", "to": "/hr-eis/notifications",
     "required_permission": "hr_eis.notification.view_self", "sort_order": 35},

    # -- approving authorities --------------------------------------------
    {"code": "hr_eis.pending_requests", "label": "Pending Approvals",
     "icon": "FaTasks", "to": "/hr-eis/pending",
     "required_permission": "hr_eis.leave.decide", "sort_order": 50},

    # -- HR Administrator --------------------------------------------------
    {"code": "hr_eis.service_records", "label": "Service Records",
     "icon": "FaUsers", "to": "/hr-eis/service-records",
     "required_permission": "hr_eis.service_record.manage", "sort_order": 60},
    {"code": "hr_eis.verify_claims", "label": "Verify Claims",
     "icon": "FaCheck", "to": "/hr-eis/verify",
     "required_permission": "hr_eis.ltc.verify", "sort_order": 65},
    {"code": "hr_eis.assign_reviewers", "label": "Assign Appraisal Reviewers",
     "icon": "FaUserTag", "to": "/hr-eis/appraisal-reviewers",
     "required_permission": "hr_eis.appraisal.assign_reviewer", "sort_order": 70},
    {"code": "hr_eis.audit", "label": "Audit & Compliance",
     "icon": "FaChartLine", "to": "/hr-eis/audit",
     "required_permission": "hr_eis.audit.view", "sort_order": 75},
    {"code": "hr_eis.workflow_config", "label": "Workflow Configuration",
     "icon": "FaCogs", "to": "/hr-eis/workflow-config",
     "required_permission": "hr_eis.workflow.configure", "sort_order": 80},

    # -- Accountant --------------------------------------------------------
    {"code": "hr_eis.financial_processing", "label": "Financial Processing",
     "icon": "FaMoneyBill", "to": "/hr-eis/financial-processing",
     "required_permission": "hr_eis.ltc.process", "sort_order": 85},
]

#: Every permission this module recognises.
PERMISSIONS = [
    ("hr_eis.service_record.view", "View an employee service record"),
    ("hr_eis.service_record.manage", "Create and update service records"),
    ("hr_eis.leave.apply", "Apply for leave"),
    ("hr_eis.leave.view_self", "View one's own leave requests"),
    ("hr_eis.leave.view", "View leave requests"),
    ("hr_eis.leave.decide", "Approve, reject or forward leave requests"),
    ("hr_eis.appraisal.submit", "Submit a yearly appraisal"),
    ("hr_eis.appraisal.view_self", "View one's own appraisals"),
    ("hr_eis.appraisal.view", "View appraisals"),
    ("hr_eis.appraisal.assign_reviewer", "Assign appraisal reviewers"),
    ("hr_eis.appraisal.decide", "Review and finalize appraisals"),
    ("hr_eis.ltc.apply", "Apply for LTC"),
    ("hr_eis.ltc.view_self", "View one's own LTC requests"),
    ("hr_eis.ltc.view", "View LTC requests"),
    ("hr_eis.ltc.verify", "Verify LTC documentation and eligibility"),
    ("hr_eis.ltc.decide", "Approve, reject or forward LTC requests"),
    ("hr_eis.ltc.process", "Process approved LTC claims"),
    ("hr_eis.cpda.apply", "Apply for CPDA"),
    ("hr_eis.cpda.view_self", "View one's own CPDA requests"),
    ("hr_eis.cpda.view", "View CPDA requests"),
    ("hr_eis.cpda.verify", "Verify CPDA claims"),
    ("hr_eis.cpda.decide", "Approve, reject or forward CPDA requests"),
    ("hr_eis.cpda.process", "Process approved CPDA claims"),
    ("hr_eis.notification.view_self", "View one's own notifications"),
    ("hr_eis.audit.view", "View audit and compliance logs"),
    ("hr_eis.workflow.configure", "Configure HR-EIS workflow settings"),
]

SYSTEM_PERMISSIONS = []

_EMPLOYEE = [
    "hr_eis.service_record.view",
    "hr_eis.leave.apply", "hr_eis.leave.view_self",
    "hr_eis.appraisal.submit", "hr_eis.appraisal.view_self",
    "hr_eis.ltc.apply", "hr_eis.ltc.view_self",
    "hr_eis.cpda.apply", "hr_eis.cpda.view_self",
    "hr_eis.notification.view_self",
]

_AUTHORITY = [
    "hr_eis.leave.view", "hr_eis.leave.decide",
    "hr_eis.appraisal.view", "hr_eis.appraisal.decide",
    "hr_eis.ltc.view", "hr_eis.ltc.decide",
    "hr_eis.cpda.view", "hr_eis.cpda.decide",
]

_HR_ADMIN = [
    "hr_eis.service_record.view", "hr_eis.service_record.manage",
    "hr_eis.leave.view",
    "hr_eis.appraisal.view", "hr_eis.appraisal.assign_reviewer",
    "hr_eis.ltc.view", "hr_eis.ltc.verify",
    "hr_eis.cpda.view", "hr_eis.cpda.verify",
    "hr_eis.notification.view_self",
    "hr_eis.audit.view", "hr_eis.workflow.configure",
]

_ACCOUNTANT = [
    "hr_eis.ltc.view", "hr_eis.ltc.process",
    "hr_eis.cpda.view", "hr_eis.cpda.process",
]

#: Keyed by the designation name as it exists in IAM globals_designation.
ROLE_GRANTS = {
    "employee": _EMPLOYEE,
    "hod": _AUTHORITY,
    "registrar": _AUTHORITY,
    "director": _AUTHORITY,
    "hr_administrator": _HR_ADMIN,
    "accountant": _ACCOUNTANT,
}
