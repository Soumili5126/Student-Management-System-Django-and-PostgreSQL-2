from django.db import models
# Create your models here.
class Course(models.Model):
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100)

    faculty = models.ForeignKey(
        'accounts.FacultyProfile',   
        on_delete=models.SET_NULL,
        null=True,
        related_name='courses'
    )

    class Meta:
        db_table = 'academics_course'

    def __str__(self):
        return f"{self.code} - {self.name}"

class Batch(models.Model):
    name = models.CharField(max_length=100)  
    program = models.CharField(max_length=100)      
    academic_year = models.CharField(max_length=9)  
    section = models.CharField(max_length=10, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'academics_batch'
        unique_together = ('name', 'academic_year')

    def __str__(self):
        return f"{self.program} | {self.name} | {self.academic_year}"


class Enrollment(models.Model):
    student = models.ForeignKey(
        'accounts.StudentProfile',   
        on_delete=models.CASCADE,
        related_name='enrollments'
    )

    course = models.ForeignKey(
        'academics.Course',        
        on_delete=models.CASCADE
    )

    enrolled_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'academics_enrollment'
        unique_together = ('student', 'course')

    def __str__(self):
        return f"{self.student.user.username} → {self.course.code}"

class Attendance(models.Model):
    STATUS_CHOICES = (
        ('present', 'Present'),
        ('absent', 'Absent'),
    )

    student = models.ForeignKey(
        'accounts.StudentProfile',     
        on_delete=models.CASCADE,
        related_name='attendance'
    )
    course = models.ForeignKey(
        'academics.Course',            
        on_delete=models.CASCADE,
        related_name='attendance'
    )
    date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)

    class Meta:
        db_table = 'academics_attendance'
        unique_together = ('student', 'course', 'date')

    def __str__(self):
        return f"{self.student.user.username} - {self.course.code} ({self.date})"


