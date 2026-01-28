from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from datetime import timedelta
# Create your models here.
class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('faculty', 'Faculty'),
        ('student', 'Student'),
    )

    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    is_email_verified = models.BooleanField(default=False)
    profile_image = models.ImageField(upload_to='profiles/', blank=True, null=True)

    otp = models.CharField(max_length=6, blank=True, null=True)
    otp_expiry = models.DateTimeField(blank=True, null=True)
    reset_token = models.CharField(max_length=100, blank=True, null=True)
    reset_token_expiry = models.DateTimeField(blank=True, null=True)




    def __str__(self):
        return f"{self.username} ({self.role})"

class StudentProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'student'},
        related_name='student_profile'
    )
    roll_number = models.CharField(max_length=20, unique=True)
    class Meta:
        db_table = 'academics_studentprofile'  # old table

class FacultyProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'faculty'},
        related_name='faculty_profile'
    )
    department = models.CharField(max_length=100)
    designation = models.CharField(max_length=100)  # keep it
    class Meta:
        db_table = 'academics_facultyprofile'
      


