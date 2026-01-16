from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
#from escrow.models import EscrowDispute
from wallet.models import Wallet
from chat.models import Message

User = get_user_model()

class Dashboard(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='dashboard',
        limit_choices_to={'is_verified': True},
        help_text="The user owning this dashboard"
    )
    preferences = models.JSONField(
        default=dict,
        blank=True,
        help_text="User preferences for dashboard layout/widgets (e.g., {'widgets': ['wallet', 'transactions']})"
    )
    cached_metrics = models.JSONField(
        default=dict,
        blank=True,
        help_text="Cached metrics (e.g., {'total_earnings': 5000, 'pending_transactions': 2, 'unread_messages': 1})"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Dashboard"
        verbose_name_plural = "Dashboards"

    def clean(self):
        if not self.user.is_verified:
            raise ValidationError("Only verified users can have a dashboard.")
        if not (self.user.is_client or self.user.is_freelancer):
            raise ValidationError("User must be a client or freelancer to have a dashboard.")

    def __str__(self):
        return f"Dashboard for {self.user.username}"

    """def update_metrics(self):
        metrics = {}
        if hasattr(self.user, 'wallet'):
            metrics['balance'] = float(self.user.wallet.balance)
        if self.user.is_client:
            metrics['total_spent'] = float(Transaction.objects.filter(client=self.user, status='COMPLETED').aggregate(total=models.Sum('amount'))['total'] or 0)
            metrics['pending_transactions'] = Transaction.objects.filter(client=self.user, status='PENDING').count()
            metrics['open_disputes'] = EscrowDispute.objects.filter(escrow__transaction__client=self.user, status='OPEN').count()
        elif self.user.is_freelancer:
            metrics['total_earnings'] = float(Transaction.objects.filter(freelancer=self.user, status='COMPLETED').aggregate(total=models.Sum('amount'))['total'] or 0)
            metrics['pending_transactions'] = Transaction.objects.filter(freelancer=self.user, status='PENDING').count()
            metrics['open_disputes'] = EscrowDispute.objects.filter(escrow__transaction__freelancer=self.user, status='OPEN').count()
        metrics['unread_messages'] = Message.objects.filter(recipient=self.user, is_read=False).count()
        self.cached_metrics = metrics
        self.save()"""