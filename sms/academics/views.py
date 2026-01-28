from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from accounts.decorators import role_required
from accounts.models import StudentProfile

# Create your views here.
@login_required
@role_required(['student'])
def student_courses(request):
    profile = StudentProfile.objects.get(user=request.user)
    enrollments = profile.enrollments.select_related('course')

    return render(request, 'academics/student_courses.html', {
        'enrollments': enrollments
    })
