from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'skills', views.SkillViewSet, basename='skill')
router.register(r'badges', views.SkillBadgeViewSet, basename='skill-badge')
router.register(r'my-badges', views.UserSkillBadgeViewSet, basename='user-skill-badge')

urlpatterns = [
    # Job endpoints
    path('', views.JobListCreateView.as_view(), name='job-list-create'),
    path('<int:pk>/', views.JobRetrieveUpdateDestroyView.as_view(), name='job-detail'),
    path('<int:pk>/status/', views.JobUpdateStatusView.as_view(), name='job-update-status'),

    # Public badges for a user
    path('user/<int:user_id>/badges/', views.PublicUserBadgesView.as_view(), name='public-user-badges'),

    # Include router URLs
    path('', include(router.urls)),
]
