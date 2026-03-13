
import random
from django.utils import timezone
from datetime import timedelta
import uuid
from .models import Notification

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