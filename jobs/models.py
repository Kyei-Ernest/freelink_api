from django.db import models
from django.conf import settings


class Job(models.Model):
    """A job posted by a client."""
    JOB_STATUS = (
        ('available', 'Available'),
        ('pending', 'Pending'),          # At least one proposal is under review
        ('in_progress', 'In Progress'),  # A proposal has been accepted
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )

    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='jobs_posted',
        limit_choices_to={'is_client': True}  # Ensure only clients can post
    )
    freelancer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='jobs_taken',
        null=True,
        blank=True,
        limit_choices_to={'is_freelancer': True}  # Assigned freelancer
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    budget = models.DecimalField(max_digits=10, decimal_places=2)
    duration = models.PositiveIntegerField(null=True, blank=True, help_text="Estimated duration in days")
    deadline = models.DateTimeField(null=True, blank=True)
    skills_required = models.ManyToManyField("Skill", blank=True, related_name="jobs")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=20, choices=JOB_STATUS, default='available')

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at'], name='job_status_created_idx'),
            models.Index(fields=['client', 'status'], name='job_client_status_idx'),
            models.Index(fields=['freelancer', 'status'], name='job_freelancer_status_idx'),
            models.Index(fields=['budget'], name='job_budget_idx'),
        ]

    def __str__(self):
        return self.title


class Skill(models.Model):
    """Reusable skill model for tagging jobs and freelancer profiles."""
    CATEGORY_CHOICES = [
        ('development', 'Development'),
        ('design', 'Design'),
        ('writing', 'Writing'),
        ('marketing', 'Marketing'),
        ('video', 'Video & Animation'),
        ('music', 'Music & Audio'),
        ('business', 'Business'),
        ('other', 'Other'),
    ]

    name = models.CharField(max_length=50, unique=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other')
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True, help_text="Icon class name (e.g., 'fa-python')")
    is_popular = models.BooleanField(default=False, help_text="Featured in popular skills list")

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class SkillBadge(models.Model):
    """
    Verification badge for a skill.
    Users earn badges by passing tests or completing verified work.
    """
    BADGE_LEVEL = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
        ('expert', 'Expert'),
    ]

    VERIFICATION_METHOD = [
        ('test', 'Online Test'),
        ('portfolio', 'Portfolio Review'),
        ('work_history', 'Work History'),
        ('certificate', 'External Certificate'),
        ('admin', 'Admin Verified'),
    ]

    skill = models.ForeignKey(Skill, on_delete=models.CASCADE, related_name='badges')
    level = models.CharField(max_length=20, choices=BADGE_LEVEL)
    name = models.CharField(max_length=100, help_text="e.g., 'Certified Python Developer'")
    description = models.TextField(blank=True)
    icon_color = models.CharField(max_length=20, default='#4CAF50', help_text="Badge color (hex)")
    verification_method = models.CharField(max_length=20, choices=VERIFICATION_METHOD, default='test')
    passing_score = models.PositiveIntegerField(default=70, help_text="Minimum % to pass (for tests)")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['skill__name', 'level']
        unique_together = ['skill', 'level']

    def __str__(self):
        return f"{self.name} ({self.get_level_display()})"


class UserSkillBadge(models.Model):
    """
    Links a user to their earned skill badges.
    Tracks verification status and expiry.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending Verification'),
        ('verified', 'Verified'),
        ('expired', 'Expired'),
        ('revoked', 'Revoked'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='skill_badges'
    )
    badge = models.ForeignKey(SkillBadge, on_delete=models.CASCADE, related_name='holders')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    score = models.PositiveIntegerField(null=True, blank=True, help_text="Test score if applicable")
    certificate_url = models.URLField(blank=True, null=True, help_text="Link to external certificate")
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='badges_verified'
    )
    earned_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-earned_at']
        unique_together = ['user', 'badge']

    def __str__(self):
        return f"{self.user.email} - {self.badge.name}"

    @property
    def is_valid(self):
        """Check if badge is currently valid."""
        from django.utils import timezone
        if self.status != 'verified':
            return False
        if self.expires_at and self.expires_at < timezone.now():
            return False
        return True
