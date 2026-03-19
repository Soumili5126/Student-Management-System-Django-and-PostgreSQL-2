
import random
from django.utils import timezone
from datetime import timedelta
import uuid
from .models import Notification,User


def generate_otp():
    return str(random.randint(100000, 999999))


def get_otp_expiry():
    return timezone.now() + timedelta(minutes=2)

def generate_reset_token():
    return str(uuid.uuid4())

def create_notification(user, title, message, link=None):
    Notification.objects.create(
        user=user,
        title=title,
        message=message,
        link=link
    )
def create_admin_notification(title, message, link=None):
    admins = User.objects.filter(
        role__name__iexact="admin"
    )

    notifications = [
        Notification(
            user=admin,
            title=title,
            message=message,
            link=link
        )
        for admin in admins
    ]

    Notification.objects.bulk_create(notifications)


