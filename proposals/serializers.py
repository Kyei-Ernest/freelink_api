from rest_framework import serializers
from .models import Proposal


class ProposalSerializer(serializers.ModelSerializer):
    """
    Serializer for freelancers to submit proposals
    and for clients to view them.
    """
    freelancer = serializers.StringRelatedField(read_only=True)  # Show freelancer username
    job_title = serializers.CharField(source='job.title', read_only=True)

    class Meta:
        model = Proposal
        fields = [
            'id', 'freelancer', 'job', 'job_title',
            'cover_letter', 'bid', 'estimated_time',
            'status', 'submitted_at'
        ]
        read_only_fields = ('freelancer', 'status', 'submitted_at')


class ProposalStatusSerializer(serializers.ModelSerializer):
    """
    Serializer for clients to update the proposal status
    (Accept or Decline).
    """
    class Meta:
        model = Proposal
        fields = ('status',)

    def validate_status(self, value):
        """Ensure only valid status transitions are allowed."""
        if value not in ['accepted', 'declined']:
            raise serializers.ValidationError(
                "Status can only be set to 'accepted' or 'declined'."
            )
        return value
