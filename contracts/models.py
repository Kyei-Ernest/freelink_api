import uuid
from django.db import models
from django.conf import settings
from jobs.models import Job


class Contract(models.Model):
    CONTRACT_STATUS_CHOICES = [
        ("pending_acceptance", "Pending Acceptance"),
        ("active", "Active"),
        ("rejected", "Rejected"),
        ("disputed", "Disputed"),
    ]

    ESCROW_STATUS_CHOICES = [
        ("not_funded", "Not Funded"),
        ("funded", "Funded"),
        ("released", "Released"),
        ("refunded", "Refunded"),
    ]

    CURRENCY_CHOICES = [
        ("USD", "US Dollar"),
        ("EUR", "Euro"),
        ("GBP", "British Pound"),
        ("GHS", "Ghanaian Cedi"),
        ("NGN", "Nigerian Naira"),
        ("KES", "Kenyan Shilling"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job = models.OneToOneField(Job, on_delete=models.CASCADE, related_name="contract")
    client = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="contracts_as_client")
    freelancer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="contracts_as_freelancer")

    agreed_bid = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default="USD")  # dropdown


    # Legal wording + machine-readable terms
    contract_text = models.TextField(null=True, blank=True)   # full human-readable contract
    terms = models.JSONField(default=dict)                    # structured metadata (deadlines, deliverables, etc.)

    status = models.CharField(max_length=20, choices=CONTRACT_STATUS_CHOICES, default="pending_acceptance")

    # Contract-wide escrow (for lump-sum jobs)
    escrow_status = models.CharField(max_length=20, choices=ESCROW_STATUS_CHOICES, default="not_funded")
    escrow_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    start_date = models.DateTimeField(auto_now_add=True)
    expiry_date = models.DateTimeField(null=True, blank=True)

    complete = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Contract: {self.job.title} ({self.client} ↔ {self.freelancer})"




class Milestone(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("disputed", "Disputed"),
        ("released", "Released"),
    ]

    ESCROW_STATUS_CHOICES = [
        ("not_funded", "Not Funded"),
        ("funded", "Funded"),
        ("released", "Released"),
        ("refunded", "Refunded"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, related_name="milestones")

    title = models.CharField(max_length=255)
    description = models.TextField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    due_date = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")

    # Escrow handled per milestone (avoids type mismatch)
    escrow_status = models.CharField(max_length=20, choices=ESCROW_STATUS_CHOICES, default="not_funded")
    escrow_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Milestone: {self.title} ({self.amount})"


# -------------------
# Audit Trail
# -------------------
class AuditTrail(models.Model):
    ACTION_CHOICES = [
        ("created", "Created"),
        ("updated", "Updated"),
        ("status_changed", "Status Changed"),
        ("contract_accepted", "Contract Accepted"),
        ("payment_released", "Payment Released"),
        ("dispute_opened", "Dispute Opened"),
        ("dispute_resolved", "Dispute Resolved"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    contract = models.ForeignKey(
        "contracts.Contract", on_delete=models.CASCADE, related_name="audit_trails"
    )
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    timestamp = models.DateTimeField(auto_now_add=True)

    details = models.JSONField(default=dict, blank=True)

    # Automatically generated summary (readable text)
    summary = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        if not self.summary:
            self.summary = self.generate_summary()
        super().save(*args, **kwargs)

    def generate_summary(self):
        """Generate a human-readable summary from action + details."""
        base = f"{self.get_action_display()} by {self.performed_by or 'System'}"
        if self.details:
            return f"{base} | Details: {self.details}"
        return base

    def __str__(self):
        return f"Audit: {self.contract} - {self.get_action_display()} at {self.timestamp}"


# -------------------
# Contract Documents
# -------------------
class ContractDocument(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, related_name="documents")

    document = models.FileField(upload_to="contracts/documents/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    # Version control support
    version = models.PositiveIntegerField(default=1)
    is_latest = models.BooleanField(default=True)

    def __str__(self):
        return f"Document for {self.contract} (v{self.version})"
