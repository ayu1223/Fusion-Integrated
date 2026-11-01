from django.urls import path

from modules.hr_eis.api import views as v

urlpatterns = [
    # service records
    path("service-record", v.ServiceRecordView.as_view(),
         name="hr_eis-service-record"),
    path("service-record/manage", v.ServiceRecordManageView.as_view(),
         name="hr_eis-service-record-manage"),
    path("service-record/manage/<int:user_id>", v.ServiceRecordManageView.as_view(),
         name="hr_eis-service-record-update"),

    # leave
    path("leave/requests", v.LeaveRequestListCreateView.as_view(),
         name="hr_eis-leave-requests"),
    path("leave/requests/<int:pk>/decide", v.LeaveRequestDecideView.as_view(),
         name="hr_eis-leave-decide"),

    # appraisal
    path("appraisal/requests", v.AppraisalListCreateView.as_view(),
         name="hr_eis-appraisal-requests"),
    path("appraisal/requests/<int:pk>/assign-reviewer",
         v.AppraisalAssignReviewerView.as_view(),
         name="hr_eis-appraisal-assign-reviewer"),
    path("appraisal/requests/<int:pk>/finalize",
         v.AppraisalFinalizeView.as_view(),
         name="hr_eis-appraisal-finalize"),

    # LTC
    path("ltc/requests", v.LTCRequestListCreateView.as_view(),
         name="hr_eis-ltc-requests"),
    path("ltc/requests/<int:pk>/verify", v.LTCRequestVerifyView.as_view(),
         name="hr_eis-ltc-verify"),
    path("ltc/requests/<int:pk>/decide", v.LTCRequestDecideView.as_view(),
         name="hr_eis-ltc-decide"),
    path("ltc/requests/<int:pk>/process", v.LTCRequestProcessView.as_view(),
         name="hr_eis-ltc-process"),

    # CPDA
    path("cpda/requests", v.CPDARequestListCreateView.as_view(),
         name="hr_eis-cpda-requests"),
    path("cpda/requests/<int:pk>/verify", v.CPDARequestVerifyView.as_view(),
         name="hr_eis-cpda-verify"),
    path("cpda/requests/<int:pk>/decide", v.CPDARequestDecideView.as_view(),
         name="hr_eis-cpda-decide"),
    path("cpda/requests/<int:pk>/process", v.CPDARequestProcessView.as_view(),
         name="hr_eis-cpda-process"),

    # notifications, audit, workflow config
    path("notifications", v.NotificationListView.as_view(),
         name="hr_eis-notifications"),
    path("audit-logs", v.AuditLogListView.as_view(),
         name="hr_eis-audit-logs"),
    path("workflow-config", v.WorkflowConfigView.as_view(),
         name="hr_eis-workflow-config"),
]
