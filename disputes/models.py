import uuid
from django.db import models
from django.conf import settings
from contracts.models import Contract


class Dispute(models.Model):
    """
    A dispute raised by a client or freelancer on a contract.
    """
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('under_review', 'Under Review'),
        ('resolved_client', 'Resolved in Favor of Client'),
        ('resolved_freelancer', 'Resolved in Favor of Freelancer'),
        ('resolved_compromise', 'Resolved by Compromise'),
        ('closed', 'Closed'),
    ]

    REASON_CHOICES = [
        ('quality', 'Quality of Work'),
        ('deadline', 'Missed Deadline'),
        ('payment', 'Payment Issue'),
        ('communication', 'Communication Problems'),
        ('scope', 'Scope Disagreement'),
        ('other', 'Other'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    contract = models.ForeignKey(
        Contract,
        on_delete=models.CASCADE,
        related_name='disputes'
    )
    raised_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='disputes_raised'
    )
    reason = models.CharField(max_length=20, choices=REASON_CHOICES)
    description = models.TextField(help_text="Detailed description of the dispute")
    evidence = models.FileField(
        upload_to='disputes/evidence/',
        blank=True,
        null=True,
        help_text="Supporting documents or screenshots"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    resolution_notes = models.TextField(blank=True, help_text="Notes on how the dispute was resolved")
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='disputes_resolved'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Dispute'
        verbose_name_plural = 'Disputes'

    def __str__(self):
        return f"Dispute: {self.contract} - {self.get_reason_display()} ({self.get_status_display()})"


class DisputeComment(models.Model):
    """
    Comments on a dispute by involved parties or admin.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    dispute = models.ForeignKey(
        Dispute,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='dispute_comments'
    )
    content = models.TextField()
    attachment = models.FileField(
        upload_to='disputes/comments/',
        blank=True,
        null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Comment by {self.author.email} on {self.dispute}"
