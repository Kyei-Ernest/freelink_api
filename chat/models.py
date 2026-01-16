from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

User = get_user_model()

class Message(models.Model):
    """
    Represents a message sent from one user to another.
    """
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_messages',
        limit_choices_to={'is_verified': True},  # Only verified users can send
        help_text="The user sending the message"
    )
    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='received_messages',
        limit_choices_to={'is_verified': True},  # Only verified users can receive
        help_text="The user receiving the message"
    )
    content = models.TextField(
        max_length=2000,
        help_text="Message content"
    )
    is_received = models.BooleanField(
        default=True,
        help_text="Whether the message has been received by the server"
    )
    is_read = models.BooleanField(
        default=False,
        help_text="Whether the recipient has read the message"
    )
    created_at = models.DateTimeField(auto_now_add=True)  # Timestamp when created
    updated_at = models.DateTimeField(auto_now=True)      # Timestamp when updated

    def mark_as_read(self):
        """Mark message as read."""
        self.is_read = True
        self.save(update_fields=['is_read'])

    class Meta:
        verbose_name = "Message"
        verbose_name_plural = "Messages"
        ordering = ['created_at']

    def clean(self):
        """
        Extra validation before saving.
        """
        if not self.sender.is_verified or not self.recipient.is_verified:
            raise ValidationError("Both sender and recipient must be verified.")
        if self.sender == self.recipient:
            raise ValidationError("Sender and recipient cannot be the same user.")
        if not (self.sender.is_client or self.sender.is_freelancer or self.sender.is_staff):
            raise ValidationError("Sender must be a client, freelancer, or admin.")
        if not (self.recipient.is_client or self.recipient.is_freelancer or self.recipient.is_staff):
            raise ValidationError("Recipient must be a client, freelancer, or admin.")

    def __str__(self):
        return f"Message from {self.sender.email} to {self.recipient.email} at {self.created_at}"
