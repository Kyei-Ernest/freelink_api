from django.urls import path
from .views import (
    NotificationListView,
    UnreadNotificationListView,
    MarkNotificationReadView,
    MarkAllNotificationsReadView,
    NotificationCountView,
)

urlpatterns = [
    path('', NotificationListView.as_view(), name='notifications'),
    path('unread/', UnreadNotificationListView.as_view(), name='notifications-unread'),
    path('count/', NotificationCountView.as_view(), name='notifications-count'),
    path('<int:pk>/read/', MarkNotificationReadView.as_view(), name='notification-mark-read'),
    path('read-all/', MarkAllNotificationsReadView.as_view(), name='notifications-mark-all-read'),
]