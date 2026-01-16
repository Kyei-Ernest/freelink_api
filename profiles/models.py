from django.db import models
from django.conf import settings
from django.db.models import Avg
from decimal import Decimal


class Profile(models.Model):
    """
    Unified profile for both freelancers and clients.
    Extra fields can be role-specific but live in one place.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile"
    )

    # Common fields
    bio = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to="profiles/", blank=True, null=True)
    location = models.CharField(max_length=255, blank=True)
    website = models.URLField(blank=True, null=True)

    # Freelancer-specific
    skills = models.JSONField(default=list, blank=True)
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    experience_years = models.PositiveIntegerField(default=0)

    # Client-specific
    company_name = models.CharField(max_length=255, blank=True)
    company_description = models.TextField(blank=True)

    # Tracking
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def is_freelancer(self):
        return self.user.is_freelancer

    def is_client(self):
        return self.user.is_client

    def __str__(self):
        return f"{self.user.full_name} - {'Freelancer' if self.user.is_freelancer else 'Client'}"


class UserStats(models.Model):
    """
    Track user performance metrics.
    Automatically calculated from user actions.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="stats"
    )

    # Response Time Tracking
    total_messages_received = models.PositiveIntegerField(default=0)
    total_response_time_seconds = models.BigIntegerField(default=0)
    average_response_time_seconds = models.PositiveIntegerField(default=0)

    # Proposal Response Tracking (for clients)
    total_proposals_received = models.PositiveIntegerField(default=0)
    total_proposal_response_time_seconds = models.BigIntegerField(default=0)
    average_proposal_response_time_seconds = models.PositiveIntegerField(default=0)

    # Job Completion Stats (for freelancers)
    jobs_completed = models.PositiveIntegerField(default=0)
    jobs_on_time = models.PositiveIntegerField(default=0)
    on_time_delivery_rate = models.DecimalField(max_digits=5, decimal_places=2, default=100.00)

    # Ratings
    total_ratings = models.PositiveIntegerField(default=0)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)

    # Activity
    last_online = models.DateTimeField(null=True, blank=True)
    last_message_sent = models.DateTimeField(null=True, blank=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "User Stats"
        verbose_name_plural = "User Stats"

    def __str__(self):
        return f"Stats for {self.user.email}"

    @property
    def response_time_display(self):
        """Human-readable response time."""
        seconds = self.average_response_time_seconds
        if seconds == 0:
            return "No data"
        elif seconds < 60:
            return "Under a minute"
        elif seconds < 3600:
            minutes = seconds // 60
            return f"~{minutes} minute{'s' if minutes > 1 else ''}"
        elif seconds < 86400:
            hours = seconds // 3600
            return f"~{hours} hour{'s' if hours > 1 else ''}"
        else:
            days = seconds // 86400
            return f"~{days} day{'s' if days > 1 else ''}"

    def record_message_response(self, response_time_seconds):
        """Record a new message response time."""
        self.total_messages_received += 1
        self.total_response_time_seconds += response_time_seconds
        self.average_response_time_seconds = (
            self.total_response_time_seconds // self.total_messages_received
        )
        self.save(update_fields=[
            'total_messages_received',
            'total_response_time_seconds',
            'average_response_time_seconds',
            'updated_at'
        ])

    def record_proposal_response(self, response_time_seconds):
        """Record a new proposal response time (for clients)."""
        self.total_proposals_received += 1
        self.total_proposal_response_time_seconds += response_time_seconds
        self.average_proposal_response_time_seconds = (
            self.total_proposal_response_time_seconds // self.total_proposals_received
        )
        self.save(update_fields=[
            'total_proposals_received',
            'total_proposal_response_time_seconds',
            'average_proposal_response_time_seconds',
            'updated_at'
        ])

    def record_job_completion(self, on_time: bool):
        """Record a job completion."""
        self.jobs_completed += 1
        if on_time:
            self.jobs_on_time += 1
        self.on_time_delivery_rate = Decimal(
            (self.jobs_on_time / self.jobs_completed) * 100
        ).quantize(Decimal('0.01'))
        self.save(update_fields=[
            'jobs_completed', 'jobs_on_time', 'on_time_delivery_rate', 'updated_at'
        ])

    def update_rating(self):
        """Recalculate average rating from ratings table."""
        from ratings.models import Rating
        ratings = Rating.objects.filter(reviewee=self.user)
        self.total_ratings = ratings.count()
        if self.total_ratings > 0:
            avg = ratings.aggregate(Avg('rating'))['rating__avg']
            self.average_rating = Decimal(avg).quantize(Decimal('0.01'))
        else:
            self.average_rating = Decimal('0.00')
        self.save(update_fields=['total_ratings', 'average_rating', 'updated_at'])


class Referral(models.Model):
    """
    Track referrals for referral bonus system.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('registered', 'Registered'),
        ('completed', 'Completed Job'),
        ('rewarded', 'Reward Given'),
    ]

    referrer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='referrals_made'
    )
    referred_email = models.EmailField()
    referred_user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='referred_by'
    )
    referral_code = models.CharField(max_length=20, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reward_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    registered_at = models.DateTimeField(null=True, blank=True)
    rewarded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.referrer.email} -> {self.referred_email} ({self.status})"
