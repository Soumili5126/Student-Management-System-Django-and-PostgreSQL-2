from academics.models import Course

def faculty_courses(request):
    if request.user.is_authenticated and hasattr(request.user, 'faculty_profile'):
        return {
            'faculty_courses': Course.objects.filter(
                faculty=request.user.faculty_profile
            )
        }
    return {}