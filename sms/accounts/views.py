from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from .forms import UserRegisterForm, LoginForm, AssignBatchForm
from django.contrib.auth import authenticate
import random
from django import forms
from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta
from django.contrib import messages
from .models import User, FacultyProfile
from .forms import UserRegisterForm, EnrollmentEditForm,CourseForm
from .utils import generate_otp, get_otp_expiry,generate_reset_token
from django.urls import reverse
from .decorators import admin_only, faculty_only, student_only
from .decorators import role_required
from django.http import HttpResponseForbidden
from .models import User, FacultyProfile, StudentProfile,Role, Permission
from academics.models import Course, Enrollment,Attendance,Batch,Exam,Grade,Quiz,QuizQuestion,QuizAnswer,QuizAttempt,Department,Timetable
from datetime import date
from datetime import datetime
from django.db import IntegrityError
from django.shortcuts import get_object_or_404
import csv
from django.http import HttpResponse
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from django.http import HttpResponse
from academics.models import Grade
from django.template.loader import render_to_string
from weasyprint import HTML
from django.conf import settings
from django.db.models import Avg, Max
from django.contrib.auth.hashers import make_password
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.contrib.auth.models import Group


# -------- REGISTER --------
def register_view(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)

        if form.is_valid():
            user = form.save(commit=False)
            user.first_name = form.cleaned_data['first_name']
            user.last_name = form.cleaned_data['last_name']
            user.is_active = False
            user.is_email_verified = False
            user.save()

            # ---------- STUDENT ----------
            if user.role and user.role.name.lower() == 'student':

                StudentProfile.objects.get_or_create(
                    user=user,
                    defaults={
                        'roll_number': f'R{user.id}',
                        'phone': form.cleaned_data.get('phone'),
                        'date_of_birth': form.cleaned_data.get('date_of_birth'),
                        'gender': form.cleaned_data.get('gender'),
                        'address': form.cleaned_data.get('address'),
                        'admission_year': form.cleaned_data.get('admission_year'),
                    }
                )

            # ---------- FACULTY ----------
            elif user.role and user.role.name.lower() == 'faculty':

                FacultyProfile.objects.get_or_create(
                    user=user,
                    defaults={
                        'department': form.cleaned_data.get('department'),
                        'designation': form.cleaned_data.get('designation'),
                    }
                )

            # ---------- ADMIN ----------
            # no profile needed

            # ---------- OTP ----------
            otp = generate_otp()
            user.otp = otp
            user.otp_expiry = get_otp_expiry()
            user.save()

            subject = "Verify Your Email - Student Management System"

            html_content = render_to_string(
                "emails/otp_email.html",
                {"otp": otp}
            )

            text_content = strip_tags(html_content)

            email = EmailMultiAlternatives(
                subject,
                text_content,
                settings.EMAIL_HOST_USER,
                [user.email]
            ) 

            email.attach_alternative(html_content, "text/html")
            email.send()

            request.session['verify_user_id'] = user.id
            messages.success(request, "OTP sent to email")
            return redirect('verify_otp')
    else:
        form = UserRegisterForm()

    return render(request, 'accounts/register.html', {'form': form})

# -------- LOGIN --------
def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)

        if form.is_valid():
            user = form.get_user()

            print("LOGGED USER:", user.username, user.role)   
            if not user.is_email_verified:
                messages.error(request, "Please verify your email first.")
                return redirect('login')

            if not user.is_approved:
                messages.error(request, "Your account is pending admin approval.")
                return redirect('login')
            
            login(request, user)
            return redirect('dashboard')

        else:
            print("LOGIN ERRORS:", form.errors)

    else:
        form = LoginForm()

    return render(request, 'accounts/login.html', {'form': form})

# -------- LOGOUT --------
def logout_view(request):
    logout(request)
    return redirect('login')

# -------- DASHBOARD ROUTER --------
@login_required
def dashboard(request):
    user = request.user

    if not user.role:
        messages.error(request, "No role assigned. Contact admin.")
        return redirect('login')

    role_name = user.role.name.lower()

    if role_name == 'admin':
        return redirect('admin_dashboard')
    elif role_name == 'faculty':
        return redirect('faculty_dashboard')
    elif role_name == 'student':
        return redirect('student_dashboard')

    messages.error(request, "Invalid role.")
    return redirect('login')


# -------- ROLE DASHBOARDS --------
@login_required
def admin_dashboard(request):
    return render(request, 'dashboards/admin_dashboard.html')


@login_required
def faculty_dashboard(request):
    return render(request, 'dashboards/faculty_dashboard.html')


@login_required
def student_dashboard(request):
    return render(request, 'dashboards/student_dashboard.html')

# -------- OTP VERIFICATION VIEW--------
def verify_otp(request):
    user_id = request.session.get('verify_user_id')

    if not user_id:
        messages.error(request, "Session expired. Please register again.")
        return redirect('register')

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        messages.error(request, "Invalid user.")
        return redirect('register')

    if request.method == "POST":
        otp = request.POST.get("otp")

        if user.otp != otp:
            messages.error(request, "Invalid OTP.")
            return render(request, "accounts/verify_otp.html")

        if user.otp_expiry < timezone.now():
            messages.error(request, "OTP expired.")
            return redirect("register")

        # ✅ SUCCESS
        user.is_active = True
        user.is_email_verified = True
        user.otp = None
        user.otp_expiry = None
        user.save()

        # clear session
        del request.session['verify_user_id']

        messages.success(request, "Email verified successfully. You can now login.")
        return redirect("login")

    return render(request, "accounts/verify_otp.html")

# -------- Forgot Password View --------
def forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')

        try:
            user = User.objects.get(email=email)

            token = generate_reset_token()
            user.reset_token = token
            user.reset_token_expiry = timezone.now() + timedelta(minutes=15)
            user.save()

            reset_link = request.build_absolute_uri(
            reverse('reset_password', args=[token])
)


            subject = "Password Reset - Student Management System"

            html_content = render_to_string('emails/password_reset_email.html', {
                'user': user,
                'reset_link': reset_link,
                'current_year': datetime.now().year,
            })

            text_content = strip_tags(html_content)  # fallback version

            email = EmailMultiAlternatives(
                subject,
                text_content,
                settings.EMAIL_HOST_USER,
                [user.email]
            )

            email.attach_alternative(html_content, "text/html")
            email.send()


            messages.success(request, "Password reset link sent to your email.")

        except User.DoesNotExist:
            messages.error(request, "Email not found.")

    return render(request, 'accounts/forgot_password.html')

#  -------- Reset Password View --------
def reset_password(request, token):
    try:
        user = User.objects.get(reset_token=token)

        if user.reset_token_expiry < timezone.now():
            messages.error(request, "Reset link expired.")
            return redirect('forgot_password')

    except User.DoesNotExist:
        messages.error(request, "Invalid reset link.")
        return redirect('forgot_password')

    if request.method == 'POST':
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        if password1 != password2:
            messages.error(request, "Passwords do not match.")
        else:
            user.set_password(password1)
            user.reset_token = None
            user.reset_token_expiry = None
            user.save()
            # -------- SEND SUCCESS EMAIL --------
            subject = "Your Password Was Successfully Updated"

            html_content = render_to_string('emails/password_reset_success.html', {
                'user': user,
                'current_year': datetime.now().year,
            })

            text_content = strip_tags(html_content)

            email = EmailMultiAlternatives(
                subject,
                text_content,
                settings.EMAIL_HOST_USER,
                [user.email],
            )

            email.attach_alternative(html_content, "text/html")
            email.send()


            messages.success(request, "Password reset successful. Please login.")
            return redirect('login')

    return render(request, 'accounts/reset_password.html')

# -----Role-based access-----
@login_required
@admin_only
def admin_dashboard(request):
    return render(request, 'dashboards/admin_dashboard.html')

@login_required
@faculty_only
def faculty_dashboard(request):
    return render(request, 'dashboards/faculty_dashboard.html')

@login_required
@student_only
def student_dashboard(request):
    return render(request, 'dashboards/student_dashboard.html')

@login_required
@role_required(['admin'])
def admin_dashboard(request):
    return render(request, 'dashboards/admin_dashboard.html')

@login_required
@role_required(['faculty'])
def faculty_dashboard(request):
    return render(request, 'dashboards/faculty_dashboard.html')

@login_required
@role_required(['student'])
def student_dashboard(request):
    return render(request, 'dashboards/student_dashboard.html')

# -----Admin,Faculty and Student Dashboards-----
def approve_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    user.is_approved = True
    user.is_active = True
    user.save()
    return redirect('admin_dashboard')
@login_required
def admin_dashboard(request):
    if not request.user.role or request.user.role.name.lower() != 'admin':
        return HttpResponseForbidden(render(request, '403.html'))
    

    courses = Course.objects.all()
    pending_users = User.objects.filter(
        is_approved=False,
        role__name__iexact='Faculty'
    )
    course_data = []
    for course in courses:
        enrollments = Enrollment.objects.filter(course=course).select_related(
            'student', 'student__user'
        
        )
        course_data.append({
            'course': course,
            'enrollments': enrollments
        })

    context = {
        'total_students': User.objects.filter(
            role__name__iexact='Student'
        ).count(),
        'total_faculty': User.objects.filter(
            role__name__iexact='Faculty'
        ).count(),

        'total_courses': courses.count(),
        'course_data': course_data,
        'pending_users':pending_users
         
    }

    return render(request, 'dashboards/admin_dashboard.html', context)

@login_required
def faculty_dashboard(request):

    # Proper role check
    if not request.user.role or request.user.role.name.lower() != 'faculty':
        return render(request, '403.html', status=403)

    try:
        faculty = request.user.faculty_profile
    except FacultyProfile.DoesNotExist:
        return render(request, '403.html', status=403)

    courses = Course.objects.filter(faculty=faculty)
    exams = Exam.objects.filter(course__faculty=faculty)

    course_data = []

    for course in courses:
        enrollments = Enrollment.objects.filter(
            course=course
        ).select_related(
            'student__user',
            'student__batch'
        )

        quizzes = Quiz.objects.filter(course=course)

        course_data.append({
            'course': course,
            'enrollments': enrollments,
            'quizzes': quizzes
        })

    return render(
        request,
        'dashboards/faculty_dashboard.html',
        {
            'faculty': faculty,
            'course_data': course_data,
            'exams': exams,
        }
    )

@login_required
def student_dashboard(request):
    if not request.user.role or request.user.role.name.lower() != 'student':
        return HttpResponseForbidden(render(request, '403.html'))

    try:
        student = request.user.student_profile
    except StudentProfile.DoesNotExist:
        return HttpResponseForbidden(render(request, '403.html'))


    # ---------------- BASIC OBJECTS ----------------
    student = request.user.student_profile
    batch = student.batch

    enrollments = Enrollment.objects.filter(student=student)
    attendance = Attendance.objects.filter(student=student)

    grades = Grade.objects.filter(
        student=student
    ).select_related('exam', 'exam__course')

    timetable = Timetable.objects.filter(
        batch=student.batch
    ).order_by('day', 'start_time')


    # ---------------- ATTENDANCE SUMMARY ----------------
    attendance_summary = {}

    for enrollment in enrollments:
        total = Attendance.objects.filter(
            student=student,
            course=enrollment.course
        ).count()

        present = Attendance.objects.filter(
            student=student,
            course=enrollment.course,
            status='present'
        ).count()

        percentage = round((present / total) * 100, 2) if total > 0 else 0
        attendance_summary[enrollment.course.id] = percentage

    # ---------------- EXAM PERFORMANCE ----------------
    exam_grades = Grade.objects.filter(student=student)

    total_exams = exam_grades.count()
    passed_exams = 0
    exam_percentages = []

    for g in exam_grades:
        percentage = (g.marks_obtained / g.exam.total_marks) * 100
        exam_percentages.append(percentage)

        if percentage >= 40:
            passed_exams += 1

    failed_exams = total_exams - passed_exams
    avg_exam_percentage = (
        sum(exam_percentages) / len(exam_percentages)
        if exam_percentages else 0
    )

    # ---------------- QUIZZES + ATTEMPTS ----------------
    quizzes = Quiz.objects.filter(
        course__enrollment__student=student
    ).distinct()

    quiz_attempts = QuizAttempt.objects.filter(
        student=student
    ).select_related('quiz').order_by('-attempted_at')

    quiz_percentages = [
        (attempt.score / attempt.total_questions) * 100
        for attempt in quiz_attempts
        if attempt.total_questions > 0
    ]

    best_quiz_percentage = max(quiz_percentages) if quiz_percentages else 0
    avg_quiz_percentage = (
        sum(quiz_percentages) / len(quiz_percentages)
        if quiz_percentages else 0
    )
    

    total_quiz_attempts = quiz_attempts.count()
    latest_quiz = quiz_attempts.first()

    # ---------------- RENDER ----------------
    return render(
        request,
        'dashboards/student_dashboard.html',
        {
            'student': student,
            'batch': batch,
            'enrollments': enrollments,
            'attendance': attendance,
            'attendance_summary': attendance_summary,
            'grades': grades,
            'total_exams': total_exams,
            'timetable': timetable,

            # Quiz data
            'quizzes': quizzes,
            'quiz_attempts': quiz_attempts,
            'total_quiz_attempts': total_quiz_attempts,
            'latest_quiz': latest_quiz,

            # 📊 Exam chart data
            'passed_exams': passed_exams,
            'failed_exams': failed_exams,
            'avg_exam_percentage': round(avg_exam_percentage, 2),

            # 📊 Quiz chart data
            'best_quiz_score': round(best_quiz_percentage, 2),
            'avg_quiz_score': round(avg_quiz_percentage, 2),
        }
    )
@login_required
def edit_student_profile(request):

    if not request.user.role or request.user.role.name.lower() != 'student':
        return HttpResponseForbidden()

    try:
        student = request.user.student_profile
    except StudentProfile.DoesNotExist:
        return HttpResponseForbidden()

    user = request.user

    if request.method == "POST":

        new_username = request.POST.get('username')

        # Prevent empty username
        if not new_username:
            messages.error(request, "Username cannot be empty.")
            return redirect('edit_student_profile')

        # Prevent duplicate username
        if User.objects.exclude(pk=user.pk).filter(username=new_username).exists():
            messages.error(request, "Username already taken.")
            return redirect('edit_student_profile')

        # Update User
        user.username = new_username
        user.save()

        # Update StudentProfile
        student.date_of_birth = request.POST.get('date_of_birth')
        student.phone = request.POST.get('phone')
        student.gender = request.POST.get('gender')
        student.address = request.POST.get('address')
        student.save()

        messages.success(request, "Profile updated successfully.")
        return redirect('student_dashboard')

    return render(
        request,
        'dashboards/student/edit_profile.html',
        {
            'student': student,
            'user': user
        }
    )

@login_required
def mark_attendance(request, course_id):

    # 🔐 Role check
    if not request.user.role or request.user.role.name.lower() != 'faculty':
        return HttpResponseForbidden(render(request, '403.html'))

    # 🔐 Safety: ensure faculty profile exists
    try:
        faculty = request.user.faculty_profile
    except FacultyProfile.DoesNotExist:
        return HttpResponseForbidden(render(request, '403.html'))

    # 🔐 Ensure faculty owns the course
    course = get_object_or_404(
        Course,
        id=course_id,
        faculty=faculty
    )

    enrollments = Enrollment.objects.filter(course=course)

    if request.method == 'POST':
        attendance_date = request.POST.get('date')

        for enrollment in enrollments:
            status = request.POST.get(str(enrollment.student.id))

            if not status:
                continue  # Skip if no status selected

            try:
                Attendance.objects.create(
                    student=enrollment.student,
                    course=course,
                    date=attendance_date,
                    status=status
                )
            except IntegrityError:
                messages.error(
                    request,
                    f"Attendance already marked for "
                    f"{enrollment.student.user.username} on {attendance_date}"
                )

        return redirect('faculty_dashboard')

    attendance_date = request.GET.get('date', date.today())

    existing_attendance_students = Attendance.objects.filter(
        course=course,
        date=attendance_date
    ).values_list('student_id', flat=True)

    return render(
        request,
        'dashboards/mark_attendance.html',
        {
            'course': course,
            'enrollments': enrollments,
            'attendance_date': attendance_date,
            'existing_attendance_students': existing_attendance_students,
        }
    )

@login_required
def assign_faculty(request, course_id):

    # 🔐 Role check
    if not request.user.role or request.user.role.name.lower() != 'admin':
        return HttpResponseForbidden(render(request, '403.html'))

    # 🔐 Secure course lookup
    course = get_object_or_404(Course, id=course_id)

    faculties = FacultyProfile.objects.select_related('user')

    if request.method == 'POST':
        faculty_id = request.POST.get('faculty')

        faculty = get_object_or_404(
            FacultyProfile,
            id=faculty_id
        )

        course.faculty = faculty
        course.save()

        messages.success(
            request,
            f"{faculty.user.username} assigned to {course.name}"
        )

        return redirect('admin_dashboard')

    return render(
        request,
        'dashboards/assign_faculty.html',
        {
            'course': course,
            'faculties': faculties
        }
    )

@login_required
@role_required(['admin'])
def enroll_students(request, course_id):

    course = get_object_or_404(
        Course,
        id=course_id
    )

    students = StudentProfile.objects.select_related('user')

    if request.method == 'POST':
        selected_students = request.POST.getlist('students')

        for student_id in selected_students:

            student = get_object_or_404(
                StudentProfile,
                id=student_id
            )

            Enrollment.objects.get_or_create(
                student=student,
                course=course
            )

        messages.success(
            request,
            "Students enrolled successfully."
        )

        return redirect('admin_dashboard')

    return render(
        request,
        'dashboards/enroll_students.html',
        {
            'course': course,
            'students': students
        }
    )

@login_required
def edit_enrollment(request, enrollment_id):

    # Role check
    if not request.user.role or request.user.role.name.lower() != 'admin':
        return HttpResponseForbidden(render(request, '403.html'))

    enrollment = get_object_or_404(
        Enrollment,
        id=enrollment_id
    )

    if request.method == 'POST':
        form = EnrollmentEditForm(
            request.POST,
            instance=enrollment
        )

        if form.is_valid():
            form.save()
            messages.success(request, "Enrollment updated.")
            return redirect('admin_dashboard')
    else:
        form = EnrollmentEditForm(instance=enrollment)

    return render(
        request,
        'dashboards/edit_enrollment.html',
        {
            'form': form,
            'enrollment': enrollment
        }
    )


@login_required
def delete_enrollment(request, enrollment_id):

    # 🔐 Role check
    if not request.user.role or request.user.role.name.lower() != 'admin':
        return HttpResponseForbidden(render(request, '403.html'))

    enrollment = get_object_or_404(
        Enrollment,
        id=enrollment_id
    )

    enrollment.delete()

    messages.success(
        request,
        "Student removed from course."
    )

    return redirect('admin_dashboard')

@login_required
def export_attendance_csv(request, course_id):

    # 🔐 Ensure user has role
    if not request.user.role:
        return HttpResponseForbidden()

    role_name = request.user.role.name.lower()

    if role_name not in ['faculty', 'admin']:
        return HttpResponseForbidden()

    # 🔐 Safe course lookup
    course = get_object_or_404(Course, id=course_id)

    # 🔐 If faculty → ensure they own the course
    if role_name == 'faculty':
        try:
            faculty = request.user.faculty_profile
        except FacultyProfile.DoesNotExist:
            return HttpResponseForbidden()

        if course.faculty != faculty:
            return HttpResponseForbidden()

    attendance = Attendance.objects.filter(course=course)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = (
        f'attachment; filename="{course.code}_attendance.csv"'
    )

    writer = csv.writer(response)
    writer.writerow(['Student', 'Date', 'Status'])

    for a in attendance:
        writer.writerow([
            a.student.user.username,
            a.date,
            a.status
        ])

    return response

#-------------Batch Management CRUD----------------

@login_required
@role_required(['admin'])
def create_batch(request):

    if request.method == 'POST':
        Batch.objects.create(
            program=request.POST['program'],
            name=request.POST['name'],
            academic_year=request.POST['academic_year'],
            section=request.POST.get('section')
        )

        messages.success(request, "Batch created successfully")
        return redirect('batch_list')

    return render(request, 'dashboards/create_batch.html')

@login_required
@role_required(['admin'])
def assign_batch(request):

    students = StudentProfile.objects.select_related('user')
    batches = Batch.objects.all()

    if request.method == 'POST':

        student = get_object_or_404(
            StudentProfile,
            id=request.POST.get('student_id')
        )

        batch = get_object_or_404(
            Batch,
            id=request.POST.get('batch_id')
        )

        student.batch = batch
        student.save()

        messages.success(
            request,
            f"{student.user.username} assigned to batch"
        )

        return redirect('batch_list')

    return render(
        request,
        'dashboards/assign_batch.html',
        {
            'students': students,
            'batches': batches
        }
    )

@login_required
@role_required(['admin'])
def remove_student_from_batch(request, student_id):

    student = get_object_or_404(
        StudentProfile,
        id=student_id
    )

    student.batch = None
    student.save()

    messages.success(
        request,
        f"{student.user.username} removed from batch"
    )

    return redirect('batch_list')

# -----------Student Management CRUD--------------

@login_required
def admin_student_management(request):

    # Admin bypass
    if request.user.role and request.user.role.name.lower() == 'admin':
        pass

    # Faculty permission check
    elif not request.user.permissions.filter(code="manage_students").exists():
        return render(request, "403.html", status=403)

    students = StudentProfile.objects.select_related(
        'user',
        'batch'
    ).prefetch_related(
        'enrollments__course'
    )

    return render(
        request,
        'admin/student_management.html',
        {'students': students}
    )
@login_required
@role_required(['admin'])
def add_student(request):

    batches = Batch.objects.all()

    if request.method == "POST":

        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")

        roll_number = request.POST.get("roll_number")
        phone = request.POST.get("phone")
        dob = request.POST.get("date_of_birth")
        gender = request.POST.get("gender")
        address = request.POST.get("address")
        admission_year = request.POST.get("admission_year")
        batch_id = request.POST.get("batch")

        # ✅ Get Student Role object
        student_role = get_object_or_404(
            Role,
            name__iexact="Student"
        )

        # ✅ Create User with ForeignKey role
        user = User.objects.create(
            username=username,
            email=email,
            password=make_password(password),
            role=student_role,
            is_active=True,
            is_approved=True
        )

        batch = None
        if batch_id:
            batch = get_object_or_404(
                Batch,
                id=batch_id
            )

        # Create Student Profile
        StudentProfile.objects.create(
            user=user,
            roll_number=roll_number,
            phone=phone,
            date_of_birth=dob,
            gender=gender,
            address=address,
            admission_year=admission_year,
            batch=batch
        )

        messages.success(request, "Student added successfully.")
        return redirect('admin_student_management')

    return render(
        request,
        'admin/add_student.html',
        {'batches': batches}
    )

@login_required
@role_required(['admin'])
def edit_student(request, student_id):

    student = get_object_or_404(
        StudentProfile,
        id=student_id
    )

    user = student.user

    if request.method == 'POST':

        user.username = request.POST.get('username')
        user.email = request.POST.get('email')

        student.roll_number = request.POST.get('roll_number')
        student.gender = request.POST.get('gender')
        student.phone = request.POST.get('phone')
        student.date_of_birth = request.POST.get('date_of_birth')
        student.address = request.POST.get('address')
        student.admission_year = request.POST.get('admission_year')

        batch_id = request.POST.get('batch')

        if batch_id:
            batch = get_object_or_404(Batch, id=batch_id)
            student.batch = batch
        else:
            student.batch = None

        user.save()
        student.save()

        messages.success(request, "Student updated successfully.")
        return redirect('admin_student_management')

    batches = Batch.objects.all()

    return render(
        request,
        'admin/edit_student.html',
        {
            'student': student,
            'batches': batches
        }
    )


@login_required
@role_required(['admin'])
def delete_student(request, student_id):

    student = get_object_or_404(
        StudentProfile,
        id=student_id
    )

    student.user.delete()  # cascades user + profile

    messages.success(
        request,
        "Student deleted successfully."
    )

    return redirect('admin_student_management')


# -----------Faculty Management CRUD--------------
@login_required
def faculty_permission_list(request):

    if not request.user.role or request.user.role.name.lower() != 'admin':
        return HttpResponseForbidden()

    faculties = User.objects.filter(role__name__iexact='Faculty')

    return render(request, 'admin/faculty_permission_list.html', {
        'faculties': faculties
    })

@login_required
def assign_faculty_permissions(request, user_id):

    if not request.user.role or request.user.role.name.lower() != 'admin':
        return HttpResponseForbidden()

    faculty = get_object_or_404(User, id=user_id)
    permissions = Permission.objects.all()

    if request.method == "POST":
        selected_permissions = request.POST.getlist("permissions")
        faculty.permissions.set(selected_permissions)
        return redirect('faculty_permission_list')

    return render(request, 'admin/assign_permissions.html', {
        'faculty': faculty,
        'permissions': permissions
    })
@login_required
@role_required(['admin'])
def admin_faculty_management(request):

    faculty_list = FacultyProfile.objects.select_related(
        'user'
    ).prefetch_related(
        'courses'
    )

    return render(
        request,
        'admin/faculty_management.html',
        {
            'faculty_list': faculty_list
        }
    )

@login_required
@role_required(['admin'])
def add_faculty(request):

    departments = Department.objects.all()
    courses = Course.objects.all()

    if request.method == "POST":

        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")

        department_id = request.POST.get("department")
        designation = request.POST.get("designation")
        selected_courses = request.POST.getlist("courses")

        # ✅ Get Faculty Role object
        faculty_role = get_object_or_404(
            Role,
            name__iexact="Faculty"
        )

        # ✅ Create user with ForeignKey role
        user = User.objects.create(
            username=username,
            email=email,
            password=make_password(password),
            role=faculty_role,
            is_active=True,
            is_approved=True
        )

        # Safe department lookup
        department = None
        if department_id:
            department = get_object_or_404(
                Department,
                id=department_id
            )

        # Create faculty profile
        faculty = FacultyProfile.objects.create(
            user=user,
            department=department,
            designation=designation
        )

        # Assign courses safely
        for course_id in selected_courses:
            course = get_object_or_404(
                Course,
                id=course_id
            )
            course.faculty = faculty
            course.save()

        messages.success(request, "Faculty added successfully.")
        return redirect("admin_faculty_management")

    return render(
        request,
        "admin/add_faculty.html",
        {
            "departments": departments,
            "courses": courses
        }
    )

@login_required
@role_required(['admin'])
def edit_faculty(request, faculty_id):

    faculty = get_object_or_404(
        FacultyProfile,
        id=faculty_id
    )

    user = faculty.user

    assigned_courses = Course.objects.filter(
        faculty=faculty
    )

    available_courses = Course.objects.all()

    if request.method == 'POST':

        user.username = request.POST.get('username')
        user.email = request.POST.get('email')

        designation = request.POST.get('designation')
        faculty.designation = designation

        department_id = request.POST.get('department')

        if department_id:
            faculty.department = get_object_or_404(
                Department,
                id=department_id
            )
        else:
            faculty.department = None

        user.save()
        faculty.save()

        messages.success(request, "Faculty updated successfully.")
        return redirect('admin_faculty_management')

    return render(
        request,
        'admin/edit_faculty.html',
        {
            'faculty': faculty,
            'assigned_courses': assigned_courses,
            'available_courses': available_courses
        }
    )

@login_required
@role_required(['admin'])
def delete_faculty(request, faculty_id):

    faculty = get_object_or_404(
        FacultyProfile,
        id=faculty_id
    )

    faculty.user.delete()  # cascades user + faculty profile

    messages.success(
        request,
        "Faculty deleted successfully."
    )

    return redirect('admin_faculty_management')


@login_required
@role_required(['admin'])
def assign_course_to_faculty(request, faculty_id):

    faculty = get_object_or_404(
        FacultyProfile,
        id=faculty_id
    )

    if request.method == 'POST':
        course_id = request.POST.get('course_id')

        course = get_object_or_404(
            Course,
            id=course_id
        )

        course.faculty = faculty
        course.save()

        messages.success(
            request,
            f"{course.name} assigned successfully."
        )

    return redirect(
        'edit_faculty',
        faculty_id=faculty.id
    )

@login_required
@role_required(['admin'])
def remove_course_from_faculty(request, course_id):

    course = get_object_or_404(
        Course,
        id=course_id
    )

    faculty_id = course.faculty.id if course.faculty else None

    course.faculty = None
    course.save()

    messages.success(
        request,
        "Course unassigned successfully."
    )

    if faculty_id:
        return redirect('edit_faculty', faculty_id=faculty_id)

    return redirect('admin_faculty_management')


# -----------Course Management CRUD--------------

@login_required
@role_required(['admin'])
def course_management(request):

    courses = Course.objects.select_related(
        'faculty'
    ).all()

    departments = Department.objects.all()

    return render(
        request,
        'admin/course_management.html',
        {
            'courses': courses,
            'departments': departments
        }
    )


@login_required
@role_required(['admin'])
def add_course(request):

    departments = Department.objects.all()

    if request.method == "POST":

        code = request.POST.get("code")
        name = request.POST.get("name")
        department_id = request.POST.get("department")

        department = get_object_or_404(
            Department,
            id=department_id
        )

        Course.objects.create(
            code=code,
            name=name,
            department=department
        )

        messages.success(request, "Course added successfully.")
        return redirect("course_management")

    return render(
        request,
        "admin/add_course.html",
        {
            "departments": departments
        }
    )

class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['code', 'name', 'department', 'faculty']


@login_required
@role_required(['admin'])
def edit_course(request, course_id):

    course = get_object_or_404(
        Course,
        id=course_id
    )

    departments = Department.objects.all()
    faculty_list = FacultyProfile.objects.all()

    if request.method == "POST":

        course.code = request.POST.get("code")
        course.name = request.POST.get("name")

        dept_id = request.POST.get("department")
        if dept_id:
            course.department = get_object_or_404(
                Department,
                id=dept_id
            )

        faculty_id = request.POST.get("faculty")
        if faculty_id:
            course.faculty = get_object_or_404(
                FacultyProfile,
                id=faculty_id
            )
        else:
            course.faculty = None

        course.save()

        messages.success(request, "Course updated successfully.")
        return redirect("course_management")

    return render(
        request,
        "admin/edit_course.html",
        {
            "course": course,
            "departments": departments,
            "faculty_list": faculty_list,
        }
    )


@login_required
@role_required(['admin'])
def delete_course(request, course_id):

    course = get_object_or_404(
        Course,
        id=course_id
    )

    if Enrollment.objects.filter(course=course).exists():
        messages.error(
            request,
            "Cannot delete course with enrolled students."
        )
        return redirect('course_management')

    course.delete()

    messages.success(
        request,
        "Course deleted successfully."
    )

    return redirect('course_management')

# -----------Exam CRUD--------------
@login_required
@role_required(['faculty'])
def create_exam(request, course_id):

    try:
        faculty = request.user.faculty_profile
    except FacultyProfile.DoesNotExist:
        return HttpResponseForbidden()

    # Ensure faculty owns the course
    course = get_object_or_404(
        Course,
        id=course_id,
        faculty=faculty
    )

    if request.method == 'POST':

        title = request.POST.get('title')
        exam_date = request.POST.get('date')
        total_marks = request.POST.get('total_marks')

        Exam.objects.create(
            course=course,
            title=title,
            date=exam_date,
            total_marks=total_marks
        )

        messages.success(request, "Exam created successfully.")
        return redirect('faculty_dashboard')

    return render(
        request,
        'dashboards/create_exam.html',
        {'course': course}
    )

@login_required
@role_required(['faculty'])
def enter_grades(request, exam_id):

    try:
        faculty = request.user.faculty_profile
    except FacultyProfile.DoesNotExist:
        return HttpResponseForbidden()

    # Ensure faculty owns the exam
    exam = get_object_or_404(
        Exam,
        id=exam_id,
        course__faculty=faculty
    )

    enrollments = Enrollment.objects.filter(
        course=exam.course
    )

    if request.method == 'POST':

        for enrollment in enrollments:
            marks = request.POST.get(str(enrollment.student.id))

            if marks is not None:
                Grade.objects.update_or_create(
                    exam=exam,
                    student=enrollment.student,
                    defaults={
                        'marks_obtained': marks
                    }
                )

        messages.success(request, "Grades saved successfully.")
        return redirect('faculty_dashboard')

    return render(
        request,
        'dashboards/enter_grades.html',
        {
            'exam': exam,
            'enrollments': enrollments
        }
    )

@login_required
@role_required(['student'])
def export_exam_results_pdf(request):

    try:
        student = request.user.student_profile
    except StudentProfile.DoesNotExist:
        return HttpResponseForbidden()

    grades = Grade.objects.filter(
        student=student
    ).select_related(
        'exam',
        'exam__course'
    )

    html_string = render_to_string(
        'dashboards/exam_results_pdf.html',
        {
            'student': student,
            'grades': grades
        }
    )

    pdf = HTML(string=html_string).write_pdf()

    response = HttpResponse(
        pdf,
        content_type='application/pdf'
    )

    response['Content-Disposition'] = \
        'inline; filename="exam_results.pdf"'

    return response

#---------Quiz View---------------
@login_required
@role_required(['faculty'])
def create_quiz(request, course_id):

    try:
        faculty = request.user.faculty_profile
    except FacultyProfile.DoesNotExist:
        return HttpResponseForbidden()

    # Ensure faculty owns the course
    course = get_object_or_404(
        Course,
        id=course_id,
        faculty=faculty
    )

    if request.method == 'POST':

        title = request.POST.get('title')
        description = request.POST.get('description')
        total_questions = request.POST.get('total_questions')

        Quiz.objects.create(
            course=course,
            title=title,
            description=description,
            total_questions=total_questions
        )

        messages.success(request, "Quiz created successfully.")
        return redirect('faculty_dashboard')

    return render(
        request,
        'dashboards/create_quiz.html',
        {'course': course}
    )
@login_required
@role_required(['faculty'])
def add_quiz_question(request, quiz_id):

    try:
        faculty = request.user.faculty_profile
    except FacultyProfile.DoesNotExist:
        return HttpResponseForbidden()

    # Ensure faculty owns this quiz via course
    quiz = get_object_or_404(
        Quiz,
        id=quiz_id,
        course__faculty=faculty
    )

    questions = QuizQuestion.objects.filter(
        quiz=quiz
    )

    if request.method == 'POST':

        QuizQuestion.objects.create(
            quiz=quiz,
            question_text=request.POST.get('question_text'),
            option_a=request.POST.get('option_a'),
            option_b=request.POST.get('option_b'),
            option_c=request.POST.get('option_c'),
            option_d=request.POST.get('option_d'),
            correct_option=request.POST.get('correct_option'),
        )

        return redirect(
            'add_quiz_question',
            quiz_id=quiz.id
        )

    return render(
        request,
        'dashboards/add_quiz_question.html',
        {
            'quiz': quiz,
            'questions': questions
        }
    )
@login_required
@role_required(['faculty'])
def edit_quiz_question(request, question_id):

    try:
        faculty = request.user.faculty_profile
    except FacultyProfile.DoesNotExist:
        return HttpResponseForbidden()

    # Ensure faculty owns the question via quiz → course
    question = get_object_or_404(
        QuizQuestion,
        id=question_id,
        quiz__course__faculty=faculty
    )

    if request.method == 'POST':

        question.question_text = request.POST.get('question_text')
        question.option_a = request.POST.get('option_a')
        question.option_b = request.POST.get('option_b')
        question.option_c = request.POST.get('option_c')
        question.option_d = request.POST.get('option_d')
        question.correct_option = request.POST.get('correct_option')

        question.save()

        return redirect(
            'add_quiz_question',
            quiz_id=question.quiz.id
        )

    return render(
        request,
        'dashboards/edit_quiz_question.html',
        {'question': question}
    )

@login_required
@role_required(['faculty'])
def delete_quiz_question(request, question_id):

    try:
        faculty = request.user.faculty_profile
    except FacultyProfile.DoesNotExist:
        return HttpResponseForbidden()

    # Ensure question belongs to this faculty
    question = get_object_or_404(
        QuizQuestion,
        id=question_id,
        quiz__course__faculty=faculty
    )

    quiz_id = question.quiz.id
    question.delete()

    messages.success(request, "Question deleted successfully.")

    return redirect(
        'add_quiz_question',
        quiz_id=quiz_id
    )
@login_required
@role_required(['student'])
def attempt_quiz(request, quiz_id):

    try:
        student = request.user.student_profile
    except StudentProfile.DoesNotExist:
        return HttpResponseForbidden()

    # 🔐 Ensure quiz belongs to a course student is enrolled in
    quiz = get_object_or_404(
        Quiz,
        id=quiz_id,
        course__enrollment__student=student
    )

    questions = QuizQuestion.objects.filter(quiz=quiz)
    total_questions = questions.count()

    if request.method == "POST":

        # Create attempt
        attempt = QuizAttempt.objects.create(
            quiz=quiz,
            student=student,
            score=0,
            total_questions=total_questions
        )

        correct = 0

        for question in questions:

            selected = request.POST.get(
                f"question_{question.id}"
            )

            if not selected:
                continue

            QuizAnswer.objects.create(
                attempt=attempt,
                question=question,
                selected_option=selected
            )

            if selected == question.correct_option:
                correct += 1

        attempt.score = correct
        attempt.save()

        return redirect('quiz_result', attempt.id)

    return render(
        request,
        'dashboards/attempt_quiz.html',
        {
            'quiz': quiz,
            'questions': questions
        }
    )
@login_required
@role_required(['student'])
def quiz_result(request, attempt_id):

    try:
        student = request.user.student_profile
    except StudentProfile.DoesNotExist:
        return HttpResponseForbidden()

    attempt = get_object_or_404(
        QuizAttempt,
        id=attempt_id,
        student=student   # 🔐 Only own attempt
    )

    answers = attempt.answers.select_related('question')

    return render(
        request,
        'dashboards/quiz_result.html',
        {
            'attempt': attempt,
            'answers': answers
        }
    )
@login_required
@role_required(['faculty'])
def faculty_quiz_analytics(request, quiz_id):

    try:
        faculty = request.user.faculty_profile
    except FacultyProfile.DoesNotExist:
        return HttpResponseForbidden()

    # 🔐 Ensure quiz belongs to this faculty
    quiz = get_object_or_404(
        Quiz,
        id=quiz_id,
        course__faculty=faculty
    )

    attempts = (
        QuizAttempt.objects
        .filter(quiz=quiz)
        .select_related('student__user')
        .order_by('student', '-attempted_at')
    )

    student_stats = {}

    for attempt in attempts:

        student = attempt.student

        if student not in student_stats:
            student_stats[student] = {
                'student': student,
                'attempts': 0,
                'best_score': attempt.score,
                'latest_score': attempt.score,
                'best_percentage': attempt.percentage,
            }

        student_stats[student]['attempts'] += 1

        student_stats[student]['best_score'] = max(
            student_stats[student]['best_score'],
            attempt.score
        )

        student_stats[student]['best_percentage'] = max(
            student_stats[student]['best_percentage'],
            attempt.percentage
        )

    return render(
        request,
        'dashboards/faculty_quiz_analytics.html',
        {
            'quiz': quiz,
            'student_stats': student_stats.values()
        }
    )