from django.db import models
from django.utils import timezone


class Student(models.Model):
    name = models.CharField(max_length=100)
    roll_number = models.CharField(max_length=50, unique=True)
    email = models.EmailField(blank=True)
    course = models.CharField(max_length=100, default="BCA")
    semester = models.CharField(max_length=20, blank=True)
    photo = models.ImageField(upload_to="students/")
    registered_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.roll_number})"


class Attendance(models.Model):
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="attendances"
    )
    date = models.DateField(default=timezone.localdate)
    time = models.TimeField(auto_now_add=True)
    in_time = models.TimeField(null=True, blank=True)
    out_time = models.TimeField(null=True, blank=True)
    status = models.CharField(max_length=20, default="Present")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["student", "date"],
                name="unique_student_attendance_per_day"
            )
        ]
        ordering = ["-date", "-time"]

    def __str__(self):
        return f"{self.student.name} - {self.date} - {self.status}"
