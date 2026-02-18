from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from accounts.decorators import role_required
from accounts.models import StudentProfile,FacultyProfile
from django.http import HttpResponseForbidden
from .models import Course, Enrollment, Attendance, Department
from django.utils import timezone
from .models import Batch,Timetable
from .forms import DepartmentForm
from django.forms import modelformset_factory
from django.contrib import messages

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
                defaults={'status': status,}
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
        batch_id = request.POST.get('batch_id')
        batch = Batch.objects.get(id=batch_id)

        student.batch = batch   # ✅ THIS LINE MATTERS
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
@login_required
def department_list(request):
    if request.user.role != 'admin':
        return HttpResponseForbidden()

    departments = Department.objects.prefetch_related('courses')

    return render(
        request,
        'dashboards/admin/department_list.html',
        {'departments': departments}
    )
@login_required
def create_department(request):
    if request.user.role != 'admin':
        return HttpResponseForbidden()

    form = DepartmentForm(request.POST or None)

    if form.is_valid():
        form.save()
        return redirect('department_list')

    return render(
        request,
        'dashboards/admin/department_form.html',
        {'form': form, 'title': 'Create Department'}
    )
def edit_department(request, pk):
    department = get_object_or_404(Department, pk=pk)

    CourseFormSet = modelformset_factory(
        Course,
        fields=('code', 'name'),
        extra=1,
        can_delete=True
    )

    queryset = Course.objects.filter(department=department)

    if request.method == 'POST':
        form = DepartmentForm(request.POST, instance=department)
        formset = CourseFormSet(request.POST, queryset=queryset,prefix='courses')

        if form.is_valid() and formset.is_valid():
            form.save()

            instances = formset.save(commit=False)

            for instance in instances:
                instance.department = department
                instance.save()

            # delete marked objects
            for obj in formset.deleted_objects:
                obj.delete()

            return redirect('department_list')

    else:
        form = DepartmentForm(instance=department)
        formset = CourseFormSet(queryset=queryset,prefix='courses')

    return render(request, 'dashboards/admin/edit_department.html', {
        'form': form,
        'formset': formset,
        'department': department
    })

@login_required
def delete_department(request, pk):
    if request.user.role != 'admin':
        return HttpResponseForbidden()

    department = get_object_or_404(Department, pk=pk)
    department.delete()
    return redirect('department_list')

@login_required
def faculty_timetable(request):
    faculty = request.user.faculty_profile

    # Only show courses assigned to this faculty
    courses = Course.objects.filter(faculty=faculty)

    batches = Batch.objects.all()

    if request.method == "POST":

        Timetable.objects.create(
            batch_id=request.POST.get("batch"),
            course_id=request.POST.get("course"),
            faculty=faculty,
            day=request.POST.get("day"),
            start_time=request.POST.get("start_time"),
            end_time=request.POST.get("end_time"),
        )

        return redirect("faculty_timetable")

    timetables = Timetable.objects.filter(faculty=faculty).order_by('day', 'start_time')

    return render(request, "dashboards/faculty/timetable.html", {
        "courses": courses,
        "batches": batches,
        "timetables": timetables
    })
@login_required
def admin_timetable(request):

    if request.user.role != 'admin':
        return redirect('dashboard')

    timetables = Timetable.objects.select_related(
        'batch',
        'course',
        'faculty'
    ).order_by('batch', 'day', 'start_time')

    batches = Batch.objects.all()
    courses = Course.objects.all()
    faculties = FacultyProfile.objects.all()

    if request.method == "POST":

        Timetable.objects.create(
            batch_id=request.POST.get("batch"),
            course_id=request.POST.get("course"),
            faculty_id=request.POST.get("faculty"),
            day=request.POST.get("day"),
            start_time=request.POST.get("start_time"),
            end_time=request.POST.get("end_time"),
        )

        return redirect('admin_timetable')

    return render(request, 'dashboards/admin/timetable.html', {
        'timetables': timetables,
        'batches': batches,
        'courses': courses,
        'faculties': faculties,
    })
@login_required
def edit_timetable(request, pk):

    timetable = get_object_or_404(Timetable, pk=pk)

    batches = Batch.objects.all()
    courses = Course.objects.all()
    faculties = FacultyProfile.objects.all()

    if request.method == "POST":
        timetable.batch_id = request.POST.get("batch")
        timetable.course_id = request.POST.get("course")
        timetable.faculty_id = request.POST.get("faculty")
        timetable.day = request.POST.get("day")
        timetable.start_time = request.POST.get("start_time")
        timetable.end_time = request.POST.get("end_time")
        timetable.save()

        return redirect('admin_timetable')

    return render(request, "dashboards/admin/edit_timetable.html", {
        "timetable": timetable,
        "batches": batches,
        "courses": courses,
        "faculties": faculties,
        'day_choices': Timetable.DAYS,
    })
@login_required
def delete_timetable(request, pk):
    timetable = get_object_or_404(Timetable, pk=pk)
    timetable.delete()
    return redirect('admin_timetable')
