from django.test import TestCase
from rest_framework.test import APIClient
from modules.directory.models import UserRef
from modules.elm.models import LeaveRequest

class LeaveRequestTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = UserRef.objects.create(user_id=1001)
        self.client.force_authenticate(user=self.user)

    def test_leave_request_list(self):
        LeaveRequest.objects.create(user=self.user, start_date="2023-10-01", end_date="2023-10-10", reason="Vacation", status="pending")
        response = self.client.get("/api/v1/elm/leave-requests/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_leave_request_create(self):
        response = self.client.post("/api/v1/elm/leave-requests/create/", {
            "start_date": "2023-10-11",
            "end_date": "2023-10-20",
            "reason": "Sick Leave",
            "status": "pending"
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(LeaveRequest.objects.count(), 1)
