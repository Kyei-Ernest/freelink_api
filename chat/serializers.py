from rest_framework import serializers
from .models import Message
from django.contrib.auth import get_user_model

User = get_user_model()

class MessageSerializer(serializers.ModelSerializer):
    """
    Serializer for displaying and sending messages.
    """
    sender = serializers.ReadOnlyField(source='sender.username')  # Read-only
    recipient = serializers.CharField(help_text="Username of the recipient")

    def validate_recipient(self, value):
        try:
            user = User.objects.get(username=value, is_verified=True)
        except User.DoesNotExist:
            raise serializers.ValidationError("Recipient not found or not verified.")
        if self.context['request'].user == user:
            raise serializers.ValidationError("You cannot send a message to yourself.")
        return user

    class Meta:
        model = Message
        fields = ['id', 'sender', 'recipient', 'content', 'is_read', 'is_received', 'created_at']
        read_only_fields = ['id', 'is_read', 'is_received', 'created_at']


    def create(self, validated_data):
        """
        Automatically set the sender to the logged-in user.
        """
        validated_data['sender'] = self.context['request'].user
        return super().create(validated_data)
