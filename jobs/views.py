from rest_framework import generics, permissions, viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone

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
