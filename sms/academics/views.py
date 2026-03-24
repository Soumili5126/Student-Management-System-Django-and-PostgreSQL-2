from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from accounts.decorators import role_required
from accounts.models import StudentProfile,FacultyProfile
from django.http import HttpResponseForbidden
from .models import Course, Enrollment, Attendance, Department,Exam,Grade,Batch
from django.utils import timezone
from .models import Batch,Timetable
from .forms import DepartmentForm
from django.forms import modelformset_factory
from django.contrib import messages
from accounts.decorators import permission_required
from django.db.models import Q
from django.core.paginator import Paginator
from accounts.utils import create_notification, create_admin_notification
from accounts.tasks import (
    send_exam_scheduled_email,
    send_marks_updated_email,
    send_timetable_created_email,
)
from django.db.models import Q

# Create your views here.
@login_required
@role_required(['student'])
def student_courses(request):

    try:
        profile = request.user.student_profile
    except StudentProfile.DoesNotExist:
        return HttpResponseForbidden()

    enrollments = profile.enrollments.select_related('course')

    return render(
        request,
        'academics/student_courses.html',
        {
            'enrollments': enrollments
        }
    )
@login_required
@role_required(['faculty'])
def mark_attendance(request, course_id):

    try:
        faculty = request.user.faculty_profile
    except FacultyProfile.DoesNotExist:
        return HttpResponseForbidden()

    #  Only allow faculty to mark their own course attendance
    course = get_object_or_404(
        Course,
        id=course_id,
        faculty=faculty
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
        {
            'course': course,
            'enrollments': enrollments
        }
    )
@login_required
@role_required(['admin'])
def admin_attendance_management(request, course_id):

    course = get_object_or_404(
        Course,
        id=course_id
    )

    enrollments = Enrollment.objects.filter(
        course=course
    )

    selected_date = request.GET.get('date')

    if selected_date:
        date = selected_date
    else:
        date = timezone.now().date()

    if request.method == 'POST':

        for e in enrollments:

            status = request.POST.get(
                str(e.student.id)
            )

            Attendance.objects.update_or_create(
                student=e.student,
                course=course,
                date=date,
                defaults={
                    'status': status,
                    'marked_by': request.user
                }
            )

        return redirect('admin_dashboard')

    attendance_records = Attendance.objects.filter(
        course=course,
        date=date
    )

    return render(
        request,
        'academics/admin_attendance.html',
        {
            'course': course,
            'enrollments': enrollments,
            'attendance_records': attendance_records,
            'selected_date': date
        }
    )

@login_required
@role_required(['admin'])
def admin_exam_list(request):

    search_query = request.GET.get("search", "")

    exams = Exam.objects.select_related('course').order_by('-date')

    # 🔍 SEARCH LOGIC
    if search_query:
        exams = exams.filter(
            Q(title__icontains=search_query) |
            Q(course__code__icontains=search_query)
        )

    context = {
        "exams": exams,
        "search_query": search_query
    }

    return render(request, "dashboards/admin/exam_list.html", context)

@login_required
@role_required(['admin'])
def admin_manage_grades(request, exam_id):

    exam = get_object_or_404(
        Exam,
        id=exam_id
    )

    # All students enrolled in that course
    enrollments = (
        Enrollment.objects
        .filter(course=exam.course)
        .select_related('student__user')
    )

    if request.method == "POST":

        for enrollment in enrollments:

            student = enrollment.student
            mark_value = request.POST.get(
                f"marks_{student.id}"
            )

            if mark_value:
                mark_value = int(mark_value)

                existing_grade = Grade.objects.filter(
                    exam=exam,
                    student=student
                ).first()

                if existing_grade:
                    old_marks = existing_grade.marks_obtained
                    existing_grade.marks_obtained = mark_value
                    existing_grade.save()

                    create_notification(
                        student.user,
                        "Marks Updated",
                        f"Your marks for {exam.title} have been updated",
                        "/accounts/student-dashboard/"
                    )

                    send_marks_updated_email.delay(
                        student.user.id,
                        exam.title,
                        exam.course.code,
                        exam.course.name,
                        old_marks,
                        mark_value,
                        exam.total_marks
                    )

                else:
                    Grade.objects.create(
                        exam=exam,
                        student=student,
                        marks_obtained=mark_value
                    )

        return redirect(
            'admin_manage_grades',
            exam.id
        )

    grades = Grade.objects.filter(
        exam=exam
    )

    return render(
        request,
        'dashboards/admin/manage_grades.html',
        {
            'exam': exam,
            'enrollments': enrollments,
            'grades': grades,
        }
    )

@login_required
@role_required(['admin'])
def add_exam(request):

    courses = Course.objects.all()

    if request.method == "POST":

        course_id = request.POST.get('course_id')
        title = request.POST.get('title')
        date = request.POST.get('date')
        total_marks = request.POST.get('total_marks')

        course = get_object_or_404(
            Course,
            id=course_id
        )

        exam = Exam.objects.create(
            course=course,
            title=title,
            date=date,
            total_marks=total_marks
        )
        enrollments = Enrollment.objects.filter(
        course=course
    ).select_related("student__user")

    for enrollment in enrollments:
        create_notification(
            enrollment.student.user,
            "Exam Scheduled",
            f"An exam '{exam.title}' has been scheduled for {course.code}",
            "/accounts/student-dashboard/"
        )

        send_exam_scheduled_email.delay(
            enrollment.student.user.id,
            course.code,
            course.name,
            exam.title,
            str(exam.date),
            exam.total_marks
        )

        return redirect('admin_exam_list')

    return render(
        request,
        'dashboards/admin/add_exam.html',
        {
            'courses': courses
        }
    )
@login_required
@role_required(['admin'])
def edit_exam(request, exam_id):

    exam = get_object_or_404(
        Exam,
        id=exam_id
    )

    courses = Course.objects.all()

    if request.method == "POST":

        course_id = request.POST.get('course_id')

        exam.title = request.POST.get('title')
        exam.date = request.POST.get('date')
        exam.total_marks = request.POST.get('total_marks')

        exam.course = get_object_or_404(
            Course,
            id=course_id
        )

        exam.save()

        return redirect('admin_exam_list')

    return render(
        request,
        'dashboards/admin/edit_exam.html',
        {
            'exam': exam,
            'courses': courses
        }
    )
@login_required
@role_required(['admin'])
def delete_exam(request, exam_id):

    exam = get_object_or_404(
        Exam,
        id=exam_id
    )

    exam.delete()

    return redirect('admin_exam_list')

from django.core.paginator import Paginator

@login_required
@permission_required('manage_batches')
def batch_list(request):

    batches = Batch.objects.all()

    search_query = request.GET.get("search", "")

    students = (
        StudentProfile.objects
        .select_related('batch', 'user')
    )

    if search_query:
        students = students.filter(
            user__username__icontains=search_query
        )

    # Pagination
    paginator = Paginator(students, 10)  # 10 students per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        'dashboards/batch_list.html',
        {
            'batches': batches,
            'students': page_obj,
            'page_obj': page_obj,
            'search_query': search_query,
        }
    )

@login_required
@permission_required('manage_batches')
def create_batch(request):

    if request.method == 'POST':

        Batch.objects.create(
            name=request.POST['name'],
            program=request.POST['program'],
            academic_year=request.POST['academic_year'],
            section=request.POST.get('section', '')
        )

        return redirect('batch_list')

    return render(
        request,
        'dashboards/create_batch.html'
    )

@login_required
@permission_required('manage_batches')
def assign_batch(request, student_id):

    student = get_object_or_404(
        StudentProfile,
        id=student_id
    )

    batches = Batch.objects.all()

    if request.method == 'POST':

        batch_id = request.POST.get('batch_id')

        batch = get_object_or_404(
            Batch,
            id=batch_id
        )

        student.batch = batch   # assign batch
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
@permission_required('manage_batches')
def edit_batch(request, batch_id):

    batch = Batch.objects.filter(id=batch_id).first()

    if not batch:
        messages.error(request, "Batch not found.")
        return redirect('batch_list')

    if request.method == 'POST':
        batch.program = request.POST.get('program')
        batch.name = request.POST.get('name')
        batch.academic_year = request.POST.get('academic_year')
        batch.section = request.POST.get('section')
        batch.save()

        messages.success(request, "Batch updated successfully.")
        return redirect('batch_list')

    return render(request, 'dashboards/edit_batch.html', {
        'batch': batch
    })
@login_required
@permission_required('manage_batches')
def delete_batch(request, batch_id):

    batch = get_object_or_404(Batch, id=batch_id)

    batch.delete()

    messages.success(request, "Batch deleted successfully.")

    return redirect('batch_list')
@login_required
@role_required(['admin'])
def department_list(request):

    search_query = request.GET.get("search", "")

    departments = Department.objects.prefetch_related(
        'courses'
    )

    if search_query:
        departments = departments.filter(
            Q(name__icontains=search_query) |
            Q(courses__code__icontains=search_query) |
            Q(courses__name__icontains=search_query)
        ).distinct()

    # Pagination
    paginator = Paginator(departments, 10)  # 10 departments per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        'dashboards/admin/department_list.html',
        {
            'departments': page_obj,
            'page_obj': page_obj,
            'search_query': search_query,
            'total_departments': departments.count()
        }
    )
@login_required
@role_required(['admin'])
def create_department(request):

    form = DepartmentForm(
        request.POST or None
    )

    if form.is_valid():
        form.save()
        return redirect('department_list')

    return render(
        request,
        'dashboards/admin/department_form.html',
        {
            'form': form,
            'title': 'Create Department'
        }
    )
@login_required
@role_required(['admin'])
def edit_department(request, pk):

    department = get_object_or_404(Department, pk=pk)
    courses = Course.objects.filter(department=department)
    available_courses = Course.objects.exclude(department=department)

    if request.method == "POST":

        # ---------- Update Department ----------
        department.name = request.POST.get("dept_name")
        department.save()

        # ---------- Update Existing Courses ----------
        for course in courses:
            code = request.POST.get(f"code_{course.id}")
            name = request.POST.get(f"name_{course.id}")

            if code and name:
                course.code = code
                course.name = name
                course.save()

        # ---------- Assign Existing Course ----------
        selected_course_id = request.POST.get("existing_course")

        if selected_course_id:
            selected_course = get_object_or_404(
                Course,
                id=selected_course_id
            )
            selected_course.department = department
            selected_course.save()

        return redirect("department_list")

    return render(
        request,
        "dashboards/admin/edit_department.html",
        {
            "department": department,
            "courses": courses,
            "available_courses": available_courses
        }
    )
@login_required
@role_required(['admin'])
def delete_department(request, pk):

    department = get_object_or_404(
        Department,
        pk=pk
    )

    department.delete()

    return redirect('department_list')

@login_required
@role_required(['faculty'])
def faculty_timetable(request):

    try:
        faculty = request.user.faculty_profile
    except FacultyProfile.DoesNotExist:
        return HttpResponseForbidden()

    # Only show courses assigned to this faculty
    courses = Course.objects.filter(
        faculty=faculty
    )

    batches = Batch.objects.all()

    if request.method == "POST":

        timetable = Timetable.objects.create(
            batch_id=request.POST.get("batch"),
            course_id=request.POST.get("course"),
            faculty=faculty,
            day=request.POST.get("day"),
            start_time=request.POST.get("start_time"),
            end_time=request.POST.get("end_time"),
        )

        students = StudentProfile.objects.filter(
            batch=timetable.batch
        ).select_related("user")

        for student in students:
            create_notification(
                student.user,
                "Timetable Updated",
                f"A new timetable entry for {timetable.course.code} has been added",
                "/accounts/student-dashboard/"
            )

            send_timetable_created_email.delay(
                student.user.id,
                timetable.batch.name,
                timetable.course.code,
                timetable.course.name,
                timetable.day,
                str(timetable.start_time),
                str(timetable.end_time)
            )

        return redirect("faculty_timetable")

    timetables = (
        Timetable.objects
        .filter(faculty=faculty)
        .order_by('day', 'start_time')
    )

    return render(
        request,
        "dashboards/faculty/timetable.html",
        {
            "courses": courses,
            "batches": batches,
            "timetables": timetables
        }
    )
@login_required
@role_required(['admin'])
def admin_timetable(request):

    timetables = (
        Timetable.objects
        .select_related('batch', 'course', 'faculty')
        .order_by('batch', 'day', 'start_time')
    )

    batches = Batch.objects.all()
    courses = Course.objects.all()
    faculties = FacultyProfile.objects.all()

    if request.method == "POST":

        timetable = Timetable.objects.create(
            batch_id=request.POST.get("batch"),
            course_id=request.POST.get("course"),
            faculty_id=request.POST.get("faculty"),
            day=request.POST.get("day"),
            start_time=request.POST.get("start_time"),
            end_time=request.POST.get("end_time"),
        )
        students = StudentProfile.objects.filter(
            batch=timetable.batch
        ).select_related("user")

        for student in students:
            create_notification(
                student.user,
                "Timetable Updated",
                f"A new timetable entry for {timetable.course.code} has been added",
                "/accounts/student-dashboard/"
            )

            send_timetable_created_email.delay(
                student.user.id,
                timetable.batch.name,
                timetable.course.code,
                timetable.course.name,
                timetable.day,
                str(timetable.start_time),
                str(timetable.end_time)
            )

        return redirect('admin_timetable')

    return render(
        request,
        'dashboards/admin/timetable.html',
        {
            'timetables': timetables,
            'batches': batches,
            'courses': courses,
            'faculties': faculties,
        }
    )
@login_required
@role_required(['admin'])
def edit_timetable(request, pk):

    timetable = get_object_or_404(
        Timetable,
        pk=pk
    )

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

    return render(
        request,
        "dashboards/admin/edit_timetable.html",
        {
            "timetable": timetable,
            "batches": batches,
            "courses": courses,
            "faculties": faculties,
            "day_choices": Timetable.DAYS,
        }
    )
@login_required
@role_required(['admin'])
def delete_timetable(request, pk):

    timetable = get_object_or_404(
        Timetable,
        pk=pk
    )

    timetable.delete()

    return redirect('admin_timetable')
