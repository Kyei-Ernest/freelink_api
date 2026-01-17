from rest_framework import generics, permissions
from django.db.models import Q
from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiResponse
from .models import Message
from .serializers import MessageSerializer


@extend_schema(
    tags=['Chat'],
    summary='Send a message',
    description='''
    Send a new message to another user on the platform.
    
    **Fields:**
    - `recipient`: User ID of the recipient
    - `content`: Message text
    
    **Note:** The sender is automatically set to the authenticated user.
    ''',
    examples=[
        OpenApiExample(
            'Send Message',
            value={
                "recipient": 2,
                "content": "Hello! I'm interested in discussing the project details."
            },
            request_only=True
        )
    ],
    responses={
        201: OpenApiResponse(description='Message sent successfully'),
        400: OpenApiResponse(description='Validation error'),
        404: OpenApiResponse(description='Recipient not found')
    }
)
class SendMessageView(generics.CreateAPIView):
    """
    API endpoint to send a new message.
    The sender is always the current logged-in user.
    The recipient email is provided manually in the request.
    """
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]


@extend_schema(
    tags=['Chat'],
    summary='Get inbox messages',
    description='''
    Get all messages received by the authenticated user.
    
    **Returns:** List of messages ordered by newest first.
    
    **Message fields:**
    - `id`: Message ID
    - `sender`: Sender's email
    - `content`: Message text
    - `is_read`: Whether you've read the message
    - `created_at`: Timestamp
    '''
)
class InboxView(generics.ListAPIView):
    """
    API endpoint to list all messages received by the logged-in user.
    """
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Message.objects.filter(recipient=self.request.user)


@extend_schema(
    tags=['Chat'],
    summary='Get sent messages',
    description='''
    Get all messages sent by the authenticated user.
    
    **Returns:** List of messages you have sent, ordered by newest first.
    '''
)
class SentMessagesView(generics.ListAPIView):
    """
    API endpoint to list all messages sent by the logged-in user.
    """
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Message.objects.filter(sender=self.request.user)


@extend_schema(
    tags=['Chat'],
    summary='Get conversation with user',
    description='''
    Get the complete message thread between you and another user.
    
    **Path parameter:**
    - `email`: Email of the user to view conversation with
    
    **Side effect:** Automatically marks unread messages from that user as read.
    
    **Returns:** All messages between you and the specified user, ordered chronologically.
    '''
)
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
