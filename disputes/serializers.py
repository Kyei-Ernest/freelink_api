from rest_framework import serializers
from .models import Dispute, DisputeComment
from contracts.models import Contract


class DisputeCommentSerializer(serializers.ModelSerializer):
    author_email = serializers.EmailField(source='author.email', read_only=True)
    author_name = serializers.CharField(source='author.full_name', read_only=True)

    class Meta:
        model = DisputeComment
        fields = [
            'id',
            'dispute',
            'author',
            'author_email',
            'author_name',
            'content',
            'attachment',
            'created_at',
        ]
        read_only_fields = ['id', 'author', 'created_at']


class DisputeSerializer(serializers.ModelSerializer):
    raised_by_email = serializers.EmailField(source='raised_by.email', read_only=True)
    raised_by_name = serializers.CharField(source='raised_by.full_name', read_only=True)
    contract_title = serializers.CharField(source='contract.job.title', read_only=True)
    comments = DisputeCommentSerializer(many=True, read_only=True)
    reason_display = serializers.CharField(source='get_reason_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Dispute
        fields = [
            'id',
            'contract',
            'contract_title',
            'raised_by',
            'raised_by_email',
            'raised_by_name',
            'reason',
            'reason_display',
            'description',
            'evidence',
            'status',
            'status_display',
            'resolution_notes',
            'resolved_by',
            'created_at',
            'updated_at',
            'resolved_at',
            'comments',
        ]
        read_only_fields = [
            'id', 'raised_by', 'status', 'resolution_notes',
            'resolved_by', 'created_at', 'updated_at', 'resolved_at'
        ]

    def validate_contract(self, value):
        """Ensure the user is part of the contract."""
        request = self.context.get('request')
        if request and request.user:
            if value.client != request.user and value.freelancer != request.user:
                raise serializers.ValidationError(
                    "You can only raise a dispute on contracts you are part of."
                )
            if value.status not in ['active', 'disputed']:
                raise serializers.ValidationError(
                    "Disputes can only be raised on active contracts."
                )
        return value


class DisputeCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a dispute."""

    class Meta:
        model = Dispute
        fields = ['contract', 'reason', 'description', 'evidence']

    def validate_contract(self, value):
        request = self.context.get('request')
        if request and request.user:
            if value.client != request.user and value.freelancer != request.user:
                raise serializers.ValidationError(
                    "You can only raise a dispute on contracts you are part of."
                )
            if hasattr(value, 'disputes') and value.disputes.filter(status='open').exists():
                raise serializers.ValidationError(
                    "There is already an open dispute on this contract."
                )
        return value


class DisputeResolveSerializer(serializers.Serializer):
    """Serializer for resolving a dispute."""
    status = serializers.ChoiceField(choices=[
        ('resolved_client', 'Resolved in Favor of Client'),
        ('resolved_freelancer', 'Resolved in Favor of Freelancer'),
        ('resolved_compromise', 'Resolved by Compromise'),
        ('closed', 'Closed'),
    ])
    resolution_notes = serializers.CharField(required=True)
