from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from .managers import UserManager


class User(AbstractUser):
    COUNTRY_CHOICES = [
        ("GH", "Ghana"),
        ("NG", "Nigeria"),
    ]



    username = None  # Remove username
    full_name = models.CharField(_("Full Name"), max_length=255)
    email = models.EmailField(_("Email Address"), unique=True)
    phone = models.CharField(_("Phone Number"), max_length=20, unique=True)
    country = models.CharField(
        max_length=2,
        choices=COUNTRY_CHOICES,
        default="GH",
        blank=False,  # ensure it's required
        null=False,  # ensure it's required at the DB level
    )
    is_freelancer = models.BooleanField(default=False)
    is_client = models.BooleanField(default=False)
    language_preference = models.CharField(_("Language Preference"), max_length=10, default="en")
    is_verified = models.BooleanField(default=False)
    is_phone_verified = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["full_name", "phone"]

    objects = UserManager()

    def __str__(self):
        return f"{self.full_name} ({self.email})"
