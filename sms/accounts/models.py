from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from datetime import timedelta

class Role(models.Model):
    name = models.CharField(max_length=50, unique=True)

    # dynamic permissions
    can_manage_students = models.BooleanField(default=False)
    can_manage_faculty = models.BooleanField(default=False)
    can_manage_courses = models.BooleanField(default=False)
    can_manage_attendance = models.BooleanField(default=False)
    can_view_reports = models.BooleanField(default=False)

    def __str__(self):
        return self.name

# Create your models here.
class User(AbstractUser):
    
    role = models.ForeignKey(                       # add THIS
        Role,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users'
    )
    is_email_verified = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False)
    profile_image = models.ImageField(upload_to='profiles/', blank=True, null=True)

    otp = models.CharField(max_length=6, blank=True, null=True)
    otp_expiry = models.DateTimeField(blank=True, null=True)
    reset_token = models.CharField(max_length=100, blank=True, null=True)
    reset_token_expiry = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.username} ({self.role})"

class StudentProfile(models.Model):
    GENDER_CHOICES = (
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    )

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='student_profile'
    )
    batch = models.ForeignKey(
        'academics.Batch',   # 👈 string reference
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='students'
    )

    roll_number = models.CharField(max_length=20, unique=True)

    phone = models.CharField(max_length=15, null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    admission_year = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        db_table = 'academics_studentprofile'

class FacultyProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='faculty_profile'
    )
    department = models.CharField(max_length=100)
    designation = models.CharField(max_length=100)  # keep it
    class Meta:
        db_table = 'academics_facultyprofile'
    def __str__(self):
        return f"{self.user.username} - {self.designation}"



      


