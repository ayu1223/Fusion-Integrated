from rest_framework import generics
from .models import LeaveRequest
from .serializers import LeaveRequestSerializer

class LeaveRequestListView(generics.ListAPIView):
    queryset = LeaveRequest.objects.filter(user=self.request.user)
    serializer_class = LeaveRequestSerializer

class LeaveRequestCreateView(generics.CreateAPIView):
    serializer_class = LeaveRequestSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
