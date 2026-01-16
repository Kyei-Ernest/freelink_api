from django.urls import path
from .views import SendMessageView, InboxView, SentMessagesView, MessageDetailView

urlpatterns = [
    path('send/', SendMessageView.as_view(), name='send_message'),
    path('inbox/', InboxView.as_view(), name='inbox'),
    path('sent/', SentMessagesView.as_view(), name='sent_messages'),
    path('message/<str:email>/', MessageDetailView.as_view(), name='message_detail'),
]
