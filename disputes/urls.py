from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DisputeViewSet, DisputeCommentViewSet

router = DefaultRouter()
router.register(r'', DisputeViewSet, basename='dispute')

urlpatterns = [
    path('', include(router.urls)),
    path(
        '<uuid:dispute_id>/comments/',
        DisputeCommentViewSet.as_view({'get': 'list', 'post': 'create'}),
        name='dispute-comments'
    ),
]
