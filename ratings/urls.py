from django.urls import path
from .views import RatingCreateListView

urlpatterns = [
    path('<int:user_id>/', RatingCreateListView.as_view(), name='rate-user'),
]