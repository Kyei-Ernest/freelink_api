from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.utils import timezone

from .models import Profile, UserStats

User = get_user_model()


@receiver(post_save, sender=User)
def create_user_profile_and_stats(sender, instance, created, **kwargs):
    """Create Profile and UserStats when a new user is created."""
    if created:
        Profile.objects.get_or_create(user=instance)
        UserStats.objects.get_or_create(user=instance)


@receiver(post_save, sender=User)
def update_last_online(sender, instance, **kwargs):
    """Update last online when user logs in."""
    if hasattr(instance, 'stats'):
        # Only update if it's been more than 5 minutes
        stats = instance.stats
        now = timezone.now()
        if not stats.last_online or (now - stats.last_online).seconds > 300:
            stats.last_online = now
            stats.save(update_fields=['last_online'])
