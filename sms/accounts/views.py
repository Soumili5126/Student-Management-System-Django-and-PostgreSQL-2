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
from .forms import UserRegisterForm
from .utils import generate_otp, get_otp_expiry,generate_reset_token
from django.urls import reverse
from .decorators import admin_only, faculty_only, student_only
from .decorators import role_required
from django.http import HttpResponseForbidden
from .models import User, FacultyProfile, StudentProfile
from academics.models import Course, Enrollment


# -------- REGISTER --------
def register_view(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST, request.FILES)

        if form.is_valid():
            user = form.save(commit=False)

            # Block login until email verified
            user.is_active = False
            user.is_email_verified = False

            # Generate OTP + expiry
            otp = generate_otp()
            user.otp = otp
            user.otp_expiry = get_otp_expiry()

            user.save()

            # Send OTP via Gmail SMTP
            send_mail(
                subject="OTP Verification - Student Management System",
                message=(
                    f"Hello {user.username},\n\n"
                    f"Your OTP is: {otp}\n\n"
                    f"This OTP is valid for 2 minutes.\n\n"
                    f"Student Management System"
                ),
                from_email=None,   # uses DEFAULT_FROM_EMAIL
                recipient_list=[user.email],
            )

            # Store user id in session for verification
            request.session['verify_user_id'] = user.id

            messages.success(request, "OTP sent to your email. Please verify.")
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
    if request.method == "POST":
        email = request.POST["email"]
        otp = request.POST["otp"]

        try:
            user = User.objects.get(email=email)

            if user.otp == otp and user.otp_expiry > timezone.now():
                user.is_active = True
                user.is_email_verified = True
                user.otp = None
                user.otp_expiry = None
                user.save()

                messages.success(request, "Email verified successfully. You can now login.")
                return redirect("login")

            else:
                messages.error(request, "Invalid or expired OTP")

        except User.DoesNotExist:
            messages.error(request, "User not found")

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


@login_required
def admin_dashboard(request):
    if request.user.role != 'admin':
        return HttpResponseForbidden(render(request, '403.html'))

    context = {
        'total_students': User.objects.filter(role='student').count(),
        'total_faculty': User.objects.filter(role='faculty').count(),
        'total_courses': Course.objects.count(),
    }

    return render(request, 'dashboards/admin_dashboard.html', context)

# -----Admin,Faculty and Student Dashboards-----
@login_required
def faculty_dashboard(request):
    if request.user.role != 'faculty':
        return HttpResponseForbidden(render(request, '403.html'))

    courses = Course.objects.filter(faculty=request.user)

    course_data = []
    for course in courses:
        students = Enrollment.objects.filter(course=course)
        course_data.append({
            'course': course,
            'students': students
        })

    return render(
        request,
        'dashboards/faculty_dashboard.html',
        {'course_data': course_data}
    )

@login_required
def student_dashboard(request):
    if request.user.role != 'student':
        return HttpResponseForbidden(render(request, '403.html'))

    enrollments = Enrollment.objects.filter(student=request.user)

    return render(
        request,
        'dashboards/student_dashboard.html',
        {'enrollments': enrollments}
    )
