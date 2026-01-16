from rest_framework import generics
from .models import Rating
from .serializers import RatingSerializer

class RatingCreateListView(generics.ListCreateAPIView):
    serializer_class = RatingSerializer

    def get_queryset(self):
        return Rating.objects.filter(reviewee_id=self.kwargs['user_id'])

    def perform_create(self, serializer):
        serializer.save(reviewer=self.request.user)
