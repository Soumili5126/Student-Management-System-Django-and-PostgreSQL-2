from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from accounts.decorators import role_required
from accounts.models import StudentProfile
from django.http import HttpResponseForbidden
from .models import Course, Enrollment, Attendance
from django.utils import timezone
# Create your views here.
@login_required
@role_required(['student'])
def student_courses(request):
    profile = StudentProfile.objects.get(user=request.user)
    enrollments = profile.enrollments.select_related('course')

    return render(request, 'academics/student_courses.html', {
        'enrollments': enrollments
    })
@login_required
def mark_attendance(request, course_id):
    if request.user.role != 'faculty':
        return HttpResponseForbidden()

    course = get_object_or_404(
        Course,
        id=course_id,
        faculty=request.user.faculty_profile
    )

    enrollments = Enrollment.objects.filter(course=course)
    today = timezone.now().date()

    if request.method == 'POST':
        for e in enrollments:
            status = request.POST.get(str(e.student.id))
            Attendance.objects.update_or_create(
                student=e.student,
                course=course,
                date=today,
                defaults={'status': status}
            )
        return redirect('faculty_dashboard')

    return render(
        request,
        'academics/mark_attendance.html',
        {'course': course, 'enrollments': enrollments}
    )
