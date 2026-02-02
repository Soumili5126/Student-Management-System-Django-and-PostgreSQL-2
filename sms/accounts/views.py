from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from .forms import UserRegisterForm, LoginForm
from django.contrib.auth import authenticate
import random
from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta
from django.contrib import messages
from .models import User
from .forms import UserRegisterForm, EnrollmentEditForm
from .utils import generate_otp, get_otp_expiry,generate_reset_token
from django.urls import reverse
from .decorators import admin_only, faculty_only, student_only
from .decorators import role_required
from django.http import HttpResponseForbidden
from .models import User, FacultyProfile, StudentProfile
from academics.models import Course, Enrollment,Attendance
from datetime import date
from django.db import IntegrityError
from django.shortcuts import get_object_or_404
import csv
from django.http import HttpResponse

# -------- REGISTER --------
def register_view(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)

        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.is_email_verified = False
            user.save()

            # ---------- STUDENT ----------
            if user.role == 'student':
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
            elif user.role == 'faculty':
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

            send_mail(
                subject="OTP Verification",
                message=f"Your OTP is {otp}",
                from_email=None,
                recipient_list=[user.email],
            )

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

    if user.role == 'admin':
        return redirect('admin_dashboard')
    elif user.role == 'faculty':
        return redirect('faculty_dashboard')
    elif user.role == 'student':
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


            send_mail(
                subject="Password Reset - Student Management System",
                message=f"""
                Hello {user.username},

                Click the link below to reset your password:

                {reset_link}

                This link is valid for 15 minutes.
                """,
                from_email=None,
                recipient_list=[user.email],
            )

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
@login_required
def admin_dashboard(request):
    if request.user.role != 'admin':
        return HttpResponseForbidden(render(request, '403.html'))

    courses = Course.objects.all()

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
        'total_students': User.objects.filter(role='student').count(),
        'total_faculty': User.objects.filter(role='faculty').count(),
        'total_courses': courses.count(),
        'course_data': course_data
    }

    return render(request, 'dashboards/admin_dashboard.html', context)

@login_required
def faculty_dashboard(request):
    if request.user.role != 'faculty':
        return HttpResponseForbidden(render(request, '403.html'))

    faculty = request.user.faculty_profile

    courses = Course.objects.filter(faculty=faculty)

    course_data = []
    for course in courses:
        enrollments = Enrollment.objects.filter(course=course).select_related(
            'student__user'
        )
        course_data.append({
            'course': course,
            'enrollments': enrollments
        })
    
    return render(
        request,
        'dashboards/faculty_dashboard.html',
        {
            'faculty': faculty,
            'course_data': course_data
        }
    )

@login_required
def student_dashboard(request):
    if request.user.role != 'student':
        return HttpResponseForbidden()

    #DEFINE student FIRST
    student = request.user.student_profile

    enrollments = Enrollment.objects.filter(student=student)
    attendance = Attendance.objects.filter(student=student)

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

    return render(
        request,
        'dashboards/student_dashboard.html',
        {
            'student': student,
            'enrollments': enrollments,
            'attendance': attendance,
            'attendance_summary': attendance_summary,
        }
    )

@login_required
def mark_attendance(request, course_id):
    if request.user.role != 'faculty':
        return HttpResponseForbidden(render(request, '403.html'))

    faculty = request.user.faculty_profile
    course = Course.objects.get(id=course_id, faculty=faculty)
    enrollments = Enrollment.objects.filter(course=course)

    if request.method == 'POST':
        attendance_date = request.POST.get('date')

        for enrollment in enrollments:
            status = request.POST.get(str(enrollment.student.id))

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
    if request.user.role != 'admin':
        return HttpResponseForbidden(render(request, '403.html'))

    course = Course.objects.get(id=course_id)
    faculties = FacultyProfile.objects.all()

    if request.method == 'POST':
        faculty_id = request.POST.get('faculty')
        faculty = FacultyProfile.objects.get(id=faculty_id)
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
def enroll_students(request, course_id):
    if request.user.role != 'admin':
        return HttpResponseForbidden(render(request, '403.html'))

    course = Course.objects.get(id=course_id)
    students = StudentProfile.objects.all()

    if request.method == 'POST':
        selected_students = request.POST.getlist('students')

        for student_id in selected_students:
            student = StudentProfile.objects.get(id=student_id)
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
    if request.user.role != 'admin':
        return HttpResponseForbidden(render(request, '403.html'))

    enrollment = get_object_or_404(Enrollment, id=enrollment_id)

    if request.method == 'POST':
        form = EnrollmentEditForm(request.POST, instance=enrollment)
        if form.is_valid():
            form.save()
            messages.success(request, "Enrollment updated.")
            return redirect('admin_dashboard')
    else:
        form = EnrollmentEditForm(instance=enrollment)

    return render(
        request,
        'dashboards/edit_enrollment.html',
        {'form': form, 'enrollment': enrollment}
    )

@login_required
def delete_enrollment(request, enrollment_id):
    if request.user.role != 'admin':
        return HttpResponseForbidden(render(request, '403.html'))

    enrollment = get_object_or_404(Enrollment, id=enrollment_id)

    enrollment.delete()
    messages.success(request, "Student removed from course.")

    return redirect('admin_dashboard')

@login_required
def export_attendance_csv(request, course_id):
    if request.user.role not in ['faculty', 'admin']:
        return HttpResponseForbidden()

    course = Course.objects.get(id=course_id)
    attendance = Attendance.objects.filter(course=course)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{course.code}_attendance.csv"'

    writer = csv.writer(response)
    writer.writerow(['Student', 'Date', 'Status'])

    for a in attendance:
        writer.writerow([
            a.student.user.username,
            a.date,
            a.status
        ])

    return response