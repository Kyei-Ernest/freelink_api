from django.core.mail import send_mail
from django.conf import settings
from .models import Notification

def send_email_notification(subject, message, recipient_list):
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        recipient_list,
        fail_silently=True,
    )

def create_notification(user, title, message):
    Notification.objects.create(user=user, title=title, message=message)