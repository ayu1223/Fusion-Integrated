from django.urls import path
from .views import LeaveRequestListView, LeaveRequestCreateView

urlpatterns = [
    path('leave-requests/', LeaveRequestListView.as_view(), name='leave-request-list'),
    path('leave-requests/create/', LeaveRequestCreateView.as_view(), name='leave-request-create'),
]
