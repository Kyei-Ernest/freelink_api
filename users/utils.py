from django.core.mail import send_mail
from django.conf import settings

def send_verification_email(user, uid, token):
    """Send verification email with activation link."""
    verification_link = f"http://frontend-site/verify-email/{uid}/{token}/"

    subject = "Verify your email address"
    message = f"Hi {user.username},\n\nPlease verify your email by clicking the link below:\n{verification_link}\n\nThank you!"
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [user.email]

    send_mail(subject, message, from_email, recipient_list)
