from django.contrib import admin
from accounts.models import StudentProfile, FacultyProfile
from .models import Course, Enrollment
# Register your models here.
@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'roll_number')
    search_fields = ('user__username', 'roll_number')


@admin.register(FacultyProfile)
class FacultyProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'department','get_role')
    def get_role(self, obj):
        return obj.user.role


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'faculty')


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'enrolled_on')
