from rest_framework import generics
from .models import LeaveRequest
from .serializers import LeaveRequestSerializer

class LeaveRequestListView(generics.ListAPIView):
    serializer_class = LeaveRequestSerializer

    def get_queryset(self):
        return LeaveRequest.objects.filter(user=self.request.user)

class LeaveRequestCreateView(generics.CreateAPIView):
    serializer_class = LeaveRequestSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
