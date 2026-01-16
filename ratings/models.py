from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator


class Rating(models.Model):
    """
    Rating given by one user to another after completing a job.
    """
    job = models.ForeignKey(
        'jobs.Job',
        on_delete=models.CASCADE,
        related_name='ratings'
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='given_ratings'
    )
    reviewee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='received_ratings'
    )
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Rating from 1 to 5"
    )
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['job', 'reviewer', 'reviewee'],
                name='unique_rating_per_job_reviewer_reviewee'
            )
        ]

    def __str__(self):
        return f"{self.reviewee.email} rated {self.rating}/5 by {self.reviewer.email}"