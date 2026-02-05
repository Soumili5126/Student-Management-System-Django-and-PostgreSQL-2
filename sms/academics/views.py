from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from accounts.decorators import role_required
from accounts.models import StudentProfile
from django.http import HttpResponseForbidden
from .models import Course, Enrollment, Attendance
from django.utils import timezone
from .models import Batch

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
@login_required
def batch_list(request):
    if request.user.role != 'admin':
        return HttpResponseForbidden()

    batches = Batch.objects.all()
    students = StudentProfile.objects.select_related('batch', 'user')

    return render(
        request,
        'dashboards/batch_list.html',
        {
            'batches': batches,
            'students': students
        }
    )
@login_required
def create_batch(request):
    if request.user.role != 'admin':
        return HttpResponseForbidden()

    if request.method == 'POST':
        Batch.objects.create(
            name=request.POST['name'],
            program=request.POST['program'],
            academic_year=request.POST['academic_year'],
            section=request.POST.get('section', '')
        )
        return redirect('batch_list')

    return render(request, 'dashboards/create_batch.html')
@login_required
def assign_batch(request, student_id):
    if request.user.role != 'admin':
        return HttpResponseForbidden()

    student = StudentProfile.objects.get(id=student_id)
    batches = Batch.objects.all()

    if request.method == 'POST':
        batch_id = request.POST.get('batch')
        student.batch_id = batch_id
        student.save()
        return redirect('batch_list')

    return render(
        request,
        'dashboards/assign_batch.html',
        {
            'student': student,
            'batches': batches
        }
    )
