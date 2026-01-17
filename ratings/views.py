from rest_framework import generics, permissions
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiExample, OpenApiResponse
from .models import Rating
from .serializers import RatingSerializer


@extend_schema_view(
    get=extend_schema(
        tags=['Ratings'],
        summary='List user ratings',
        description='''
        Get all ratings/reviews for a specific user.
        
        **Path parameter:**
        - `user_id`: ID of the user to get ratings for
        
        **Returns:** List of ratings with:
        - Reviewer information
        - Rating score (1-5)
        - Comment/review text
        - Job reference
        - Timestamp
        '''
    ),
    post=extend_schema(
        tags=['Ratings'],
        summary='Submit a rating',
        description='''
        Submit a rating/review for a user after completing a job.
        
        **Requirements:**
        - You can only rate users you've worked with
        - Rating must be between 1 and 5
        - One rating per job per user
        
        **Fields:**
        - `reviewee`: User ID of the person being rated
        - `job`: Job ID the rating is for
        - `rating`: Score from 1 (poor) to 5 (excellent)
        - `comment`: Written review (optional but recommended)
        ''',
        examples=[
            OpenApiExample(
                'Submit 5-Star Rating',
                value={
                    "reviewee": 2,
                    "job": 1,
                    "rating": 5,
                    "comment": "Excellent work! Delivered on time with great quality. Highly recommended!"
                },
                request_only=True
            ),
            OpenApiExample(
                'Submit 3-Star Rating',
                value={
                    "reviewee": 2,
                    "job": 1,
                    "rating": 3,
                    "comment": "Good work overall, but communication could be improved."
                },
                request_only=True
            )
        ],
        responses={
            201: OpenApiResponse(description='Rating submitted successfully'),
            400: OpenApiResponse(description='Validation error (e.g., rating out of range, already rated)')
        }
    )
)
class RatingCreateListView(generics.ListCreateAPIView):
    """List ratings for a user or create a new rating."""
    serializer_class = RatingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Rating.objects.filter(reviewee_id=self.kwargs['user_id'])

    def perform_create(self, serializer):
        serializer.save(reviewer=self.request.user)
