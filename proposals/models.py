from django.db import models
from django.conf import settings


class Proposal(models.Model):
    PROPOSAL_STATUS = (
        ('submitted', 'Submitted'),
        ('declined', 'Declined'),
        ('accepted', 'Accepted'),  # Should lead to a Contract
    )

    freelancer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='proposals_sent',
        limit_choices_to={'is_freelancer': True }
    )
    job = models.ForeignKey(
        'jobs.Job',  # Reference the Job model from the jobs app
        on_delete=models.CASCADE,
        related_name='proposals_received'
    )
    cover_letter = models.TextField()
    bid = models.DecimalField(max_digits=10, decimal_places=2)  # Freelancer's proposed amount
    estimated_time = models.CharField(max_length=100)  # e.g., "2 weeks", "1 month"
    status = models.CharField(max_length=20, choices=PROPOSAL_STATUS, default='submitted')
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-submitted_at']
        constraints = [
            models.UniqueConstraint(fields=['freelancer', 'job'], name='unique_proposal_per_job')
        ]

    def __str__(self):
        return f"Proposal by {self.freelancer} for {self.job}"

    def accept(self):
        """
        Mark this proposal as accepted, decline others for the same job,
        and assign the freelancer to the job.
        """
        self.status = 'accepted'
        self.save()

        # Decline all other proposals for the same job
        Proposal.objects.filter(job=self.job).exclude(id=self.id).update(status='declined')

        # Assign the freelancer to the job and change status
        self.job.freelancer = self.freelancer
        self.job.status = 'in_progress'
        self.job.save()
