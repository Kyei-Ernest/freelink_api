from django.db import models
from django.conf import settings


class Notification(models.Model):
    """
    Notification sent to a user about system events.
    """
    NOTIFICATION_TYPES = [
        ('job', 'Job Related'),
        ('proposal', 'Proposal'),
        ('contract', 'Contract'),
        ('payment', 'Payment'),
        ('message', 'Message'),
        ('system', 'System'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    title = models.CharField(max_length=255)
    message = models.TextField()
    notification_type = models.CharField(
        max_length=20,
        choices=NOTIFICATION_TYPES,
        default='system'
    )
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'

    def mark_as_read(self):
        """Mark notification as read."""
        self.is_read = True
        self.save(update_fields=['is_read'])

    def __str__(self):
        return f"{self.title} - {self.user.email}"
