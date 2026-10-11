from django.db import models
from modules/directory.models import UserRef

class LeaveRequest(models.Model):
    user = models.ForeignKey(UserRef, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "elm_leave_request"
        indexes = [
            models.Index(fields=["user"], name="leave_request_user_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.user} - {self.start_date} to {self.end_date}"
