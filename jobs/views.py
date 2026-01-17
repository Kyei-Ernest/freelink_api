from rest_framework import generics, permissions, viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiExample, OpenApiParameter, OpenApiResponse

from .models import Job, Skill, SkillBadge, UserSkillBadge
from .serializers import (
    JobSerializer, JobDetailSerializer, JobStatusSerializer,
    SkillSerializer, SkillBadgeSerializer,
    UserSkillBadgeSerializer, UserSkillBadgeCreateSerializer, UserSkillBadgeVerifySerializer
)


class IsClientUser(permissions.BasePermission):
    """Only allow 'client' users to perform action."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_client


class IsFreelancerUser(permissions.BasePermission):
    """Only allow 'freelancer' users to perform action."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_freelancer


class IsJobOwner(permissions.BasePermission):
    """Only allow the job owner (client) to edit/delete."""
    def has_object_permission(self, request, view, obj):
        return obj.client == request.user


class IsAdminUser(permissions.BasePermission):
    """Allow access only to admin users (is_staff=True)."""
    def has_permission(self, request, view):
        return request.user and request.user.is_staff


# ============== Job Views ==============

@extend_schema_view(
    get=extend_schema(
        tags=['Jobs'],
        summary='List all jobs',
        description='''
        Get a paginated list of all jobs on the platform.
        
        **Filtering:**
        - `?status=available` - Filter by job status
        - `?client=1` - Filter by client ID
        
        **Search:**
        - `?search=python` - Search in title and description
        
        **Ordering:**
        - `?ordering=-created_at` - Newest first (default)
        - `?ordering=budget` - Lowest budget first
        - `?ordering=-budget` - Highest budget first
        
        **Pagination:**
        - Returns 20 items per page
        - Use `?page=2` for next page
        ''',
        parameters=[
            OpenApiParameter(name='status', description='Filter by status: available, pending, in_progress, completed, cancelled', type=str),
            OpenApiParameter(name='search', description='Search in title and description', type=str),
            OpenApiParameter(name='ordering', description='Sort results: created_at, -created_at, budget, -budget', type=str),
        ]
    ),
    post=extend_schema(
        tags=['Jobs'],
        summary='Create a new job',
        description='''
        Create a new job posting. **Only clients can create jobs.**
        
        **Required fields:**
        - `title`: Job title (max 200 characters)
        - `description`: Detailed job description
        - `budget`: Maximum budget in USD
        
        **Optional fields:**
        - `duration`: Estimated duration in days
        - `deadline`: Job deadline (ISO 8601 format)
        - `skills_required`: List of skill names
        ''',
        examples=[
            OpenApiExample(
                'Create Job',
                value={
                    "title": "Build an E-commerce Website",
                    "description": "Looking for an experienced developer to build a modern e-commerce platform with payment integration.",
                    "budget": "2500.00",
                    "duration": 30,
                    "skills_required": ["Python", "Django", "React"]
                },
                request_only=True
            )
        ]
    )
)
class JobListCreateView(generics.ListCreateAPIView):
    """
    GET: List all jobs.
    POST: Create a new job (only allowed for clients).
    """
    queryset = Job.objects.select_related(
        'client', 'freelancer'
    ).prefetch_related(
        'skills_required'
    ).all()
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['status', 'client']
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'budget']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return JobSerializer
        return JobDetailSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            self.permission_classes = [permissions.IsAuthenticated, IsClientUser]
        return super().get_permissions()

    def perform_create(self, serializer):
        serializer.save(client=self.request.user)


@extend_schema_view(
    get=extend_schema(
        tags=['Jobs'],
        summary='Get job details',
        description='Retrieve detailed information about a specific job.'
    ),
    put=extend_schema(
        tags=['Jobs'],
        summary='Update job (full)',
        description='Update all job fields. Only the job owner can update.'
    ),
    patch=extend_schema(
        tags=['Jobs'],
        summary='Update job (partial)',
        description='Update selected job fields. Only the job owner can update.'
    ),
    delete=extend_schema(
        tags=['Jobs'],
        summary='Delete job',
        description='Delete a job. Only the job owner can delete. Cannot delete jobs that are in progress.'
    )
)


class JobRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET: Retrieve a job.
    PUT/PATCH: Update a job (owner only).
    DELETE: Delete a job (owner only).
    """
    queryset = Job.objects.all()
    permission_classes = [permissions.IsAuthenticated, IsJobOwner]

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return JobSerializer
        return JobDetailSerializer


class JobUpdateStatusView(generics.UpdateAPIView):
    """PATCH: Update only the job status."""
    queryset = Job.objects.all()
    serializer_class = JobStatusSerializer
    permission_classes = [permissions.IsAuthenticated, IsJobOwner]


# ============== Skill Views ==============

class SkillViewSet(viewsets.ModelViewSet):
    """
    Admin-managed skills.
    GET (all users): List/retrieve skills.
    POST/PUT/DELETE (admin only): Manage skills.
    """
    queryset = Skill.objects.all().order_by("name")
    serializer_class = SkillSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticated(), IsAdminUser()]

    @action(detail=False, methods=['get'])
    def popular(self, request):
        """Get popular/featured skills."""
        skills = Skill.objects.filter(is_popular=True).order_by('name')
        serializer = self.get_serializer(skills, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def categories(self, request):
        """Get all skill categories."""
        return Response([
            {'value': choice[0], 'label': choice[1]}
            for choice in Skill.CATEGORY_CHOICES
        ])


# ============== Skill Badge Views ==============

class SkillBadgeViewSet(viewsets.ModelViewSet):
    """
    Skill verification badges management.
    GET (all users): List/retrieve badges.
    POST/PUT/DELETE (admin only): Manage badges.
    """
    queryset = SkillBadge.objects.filter(is_active=True)
    serializer_class = SkillBadgeSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticated(), IsAdminUser()]

    @action(detail=False, methods=['get'])
    def by_skill(self, request):
        """Get badges for a specific skill."""
        skill_id = request.query_params.get('skill_id')
        if not skill_id:
            return Response({'error': 'skill_id required'}, status=400)
        badges = self.queryset.filter(skill_id=skill_id)
        serializer = self.get_serializer(badges, many=True)
        return Response(serializer.data)


class UserSkillBadgeViewSet(viewsets.ModelViewSet):
    """
    User's skill badges.
    - Freelancers can apply for badges
    - View their own badges
    - Admins can verify badges
    """
    serializer_class = UserSkillBadgeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return UserSkillBadge.objects.all()
        return UserSkillBadge.objects.filter(user=user)

    def get_serializer_class(self):
        if self.action == 'create':
            return UserSkillBadgeCreateSerializer
        if self.action == 'verify':
            return UserSkillBadgeVerifySerializer
        return UserSkillBadgeSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['patch'], permission_classes=[IsAdminUser])
    def verify(self, request, pk=None):
        """Admin action to verify or revoke a badge."""
        user_badge = self.get_object()
        serializer = UserSkillBadgeVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user_badge.status = serializer.validated_data['status']
        if 'score' in serializer.validated_data:
            user_badge.score = serializer.validated_data['score']
        user_badge.verified_by = request.user
        user_badge.verified_at = timezone.now()
        user_badge.save()

        return Response(UserSkillBadgeSerializer(user_badge).data)

    @action(detail=False, methods=['get'])
    def my_badges(self, request):
        """Get current user's verified badges."""
        badges = UserSkillBadge.objects.filter(
            user=request.user,
            status='verified'
        )
        serializer = UserSkillBadgeSerializer(badges, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def pending(self, request):
        """Admin: Get all pending badge applications."""
        if not request.user.is_staff:
            return Response({'error': 'Admin only'}, status=403)
        badges = UserSkillBadge.objects.filter(status='pending')
        serializer = UserSkillBadgeSerializer(badges, many=True)
        return Response(serializer.data)


class PublicUserBadgesView(generics.ListAPIView):
    """View another user's verified badges (public)."""
    serializer_class = UserSkillBadgeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user_id = self.kwargs.get('user_id')
        return UserSkillBadge.objects.filter(
            user_id=user_id,
            status='verified'
        )
