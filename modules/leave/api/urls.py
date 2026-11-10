from django.urls import path

from modules.leave.api import views

app_name = "leave"

urlpatterns = [
    path("requests", views.LeaveRequestView.as_view(), name="requests"),
    path("requests/<int:pk>", views.LeaveRequestDetailView.as_view(), name="request-detail"),
    path(
        "requests/<int:pk>/decision",
        views.LeaveRequestDecisionView.as_view(),
        name="request-decision",
    ),
    path("export", views.LeaveRequestExportView.as_view(), name="export"),
    path("substitutes", views.SubstituteAssignmentView.as_view(), name="substitutes"),
    path("policy", views.LeavePolicyConfigView.as_view(), name="policy"),
    path("hierarchy", views.HierarchyConfigView.as_view(), name="hierarchy"),
    path("calendar", views.HolidayRHCalendarView.as_view(), name="calendar"),
    path("balances", views.LeaveBalanceView.as_view(), name="balances"),
    path("resumptions", views.ResumptionRecordView.as_view(), name="resumptions"),
    path("offline/<int:pk>", views.OfflineSanctionRecordView.as_view(), name="offline"),
    path("sla", views.SLAConfigView.as_view(), name="sla"),
    path("tasks", views.WorkflowTaskView.as_view(), name="tasks"),
    path("tasks/<int:pk>", views.WorkflowTaskDetailView.as_view(), name="task-detail"),
    path("requests/<int:pk>/history", views.RequestActionView.as_view(), name="history"),
]
