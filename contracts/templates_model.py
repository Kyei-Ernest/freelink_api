from django.db import models
from django.conf import settings


class ProjectTemplate(models.Model):
    """
    Pre-built project/contract templates for common job types.
    Helps clients quickly create standardized contracts.
    """
    CATEGORY_CHOICES = [
        ('web_dev', 'Web Development'),
        ('mobile_dev', 'Mobile Development'),
        ('design', 'Design'),
        ('writing', 'Content Writing'),
        ('marketing', 'Digital Marketing'),
        ('video', 'Video Production'),
        ('data', 'Data & Analytics'),
        ('other', 'Other'),
    ]

    name = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    description = models.TextField()

    # Template content
    job_title_template = models.CharField(
        max_length=200,
        help_text="Template for job title, e.g., 'Build a {type} website'"
    )
    job_description_template = models.TextField(
        help_text="Template for job description with placeholders"
    )
    contract_terms_template = models.TextField(
        blank=True,
        help_text="Standard contract terms for this type of project"
    )

    # Suggested values
    suggested_budget_min = models.DecimalField(max_digits=10, decimal_places=2)
    suggested_budget_max = models.DecimalField(max_digits=10, decimal_places=2)
    suggested_duration_days = models.PositiveIntegerField(help_text="Typical duration in days")

    # Milestones template (JSON)
    milestones_template = models.JSONField(
        default=list,
        help_text="List of milestone templates [{title, description, percentage}]"
    )

    # Skills typically required
    suggested_skills = models.JSONField(
        default=list,
        help_text="List of skill names typically required"
    )

    # Usage tracking
    usage_count = models.PositiveIntegerField(default=0)
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_templates'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-usage_count', '-created_at']

    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"

    def increment_usage(self):
        """Track template usage."""
        self.usage_count += 1
        self.save(update_fields=['usage_count'])
