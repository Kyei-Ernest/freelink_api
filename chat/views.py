from rest_framework import generics, permissions
from django.db.models import Q
from .models import Message
from .serializers import MessageSerializer


class SendMessageView(generics.CreateAPIView):
    """
    API endpoint to send a new message.
    The sender is always the current logged-in user.
    The recipient email is provided manually in the request.
    """
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]


class InboxView(generics.ListAPIView):
    """
    API endpoint to list all messages received by the logged-in user.
    """
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Message.objects.filter(recipient=self.request.user)


class SentMessagesView(generics.ListAPIView):
    """
    API endpoint to list all messages sent by the logged-in user.
    """
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Message.objects.filter(sender=self.request.user)


class MessageDetailView(generics.ListAPIView):
    """
    List all messages between the logged-in user and the given user email.
    Marks as read if recipient is current viewer.
    """
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user_email = self.kwargs['email']
        current_user = self.request.user

        queryset = Message.objects.filter(
            Q(sender=current_user, recipient__email=user_email) |
            Q(sender__email=user_email, recipient=current_user)
        ).order_by('created_at')

        # Mark as read for all messages where current user is recipient
        Message.objects.filter(
            sender__email=user_email,
            recipient=current_user,
            is_read=False
        ).update(is_read=True)

        return queryset
