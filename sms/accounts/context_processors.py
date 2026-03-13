from academics.models import Course

def faculty_courses(request):
    if request.user.is_authenticated and hasattr(request.user, 'faculty_profile'):
        return {
            'faculty_courses': Course.objects.filter(
                faculty=request.user.faculty_profile
            )
        }
    return {}

def notification_count(request):
    if request.user.is_authenticated:
        unread_notifications = request.user.notifications.filter(is_read=False).count()
    else:
        unread_notifications = 0

    return {
        "unread_notifications": unread_notifications
    }