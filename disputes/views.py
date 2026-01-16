from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Q

from .models import Dispute, DisputeComment
from .serializers import (
    DisputeSerializer,
    DisputeCreateSerializer,
    DisputeResolveSerializer,
    DisputeCommentSerializer,
)


class IsDisputeParty(permissions.BasePermission):
    """
    Permission to check if user is part of the disputed contract.
    """
    def has_object_permission(self, request, view, obj):
        contract = obj.contract
        return (
            request.user == contract.client or
            request.user == contract.freelancer or
            request.user.is_staff
        )


class IsAdminUser(permissions.BasePermission):
    """Only allow admin users."""
    def has_permission(self, request, view):
        return request.user and request.user.is_staff


class DisputeViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing disputes.

    - list: List all disputes the user is involved in
    - create: Create a new dispute on a contract
    - retrieve: Get dispute details
    - resolve: Admin action to resolve a dispute
    - add_comment: Add a comment to a dispute
    """
    serializer_class = DisputeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Dispute.objects.all()
        return Dispute.objects.filter(
            Q(contract__client=user) | Q(contract__freelancer=user)
        )

    def get_serializer_class(self):
        if self.action == 'create':
            return DisputeCreateSerializer
        if self.action == 'resolve':
            return DisputeResolveSerializer
        return DisputeSerializer

    def perform_create(self, serializer):
        dispute = serializer.save(raised_by=self.request.user)
        # Update contract status to disputed
        contract = dispute.contract
        contract.status = 'disputed'
        contract.save(update_fields=['status'])

    @action(detail=True, methods=['patch'], permission_classes=[IsAdminUser])
    def resolve(self, request, pk=None):
        """
        Admin action to resolve a dispute.
        """
        dispute = self.get_object()

        if dispute.status not in ['open', 'under_review']:
            return Response(
                {'error': 'This dispute has already been resolved.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = DisputeResolveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        dispute.status = serializer.validated_data['status']
        dispute.resolution_notes = serializer.validated_data['resolution_notes']
        dispute.resolved_by = request.user
        dispute.resolved_at = timezone.now()
        dispute.save()

        # Update contract status based on resolution
        contract = dispute.contract
        if dispute.status in ['resolved_client', 'resolved_freelancer', 'resolved_compromise']:
            contract.status = 'active'  # or 'completed' depending on business logic
        elif dispute.status == 'closed':
            contract.status = 'active'
        contract.save(update_fields=['status'])

        return Response(DisputeSerializer(dispute).data)

    @action(detail=True, methods=['post'])
    def add_comment(self, request, pk=None):
        """
        Add a comment to a dispute.
        """
        dispute = self.get_object()

        # Check if user is part of the dispute
        if not IsDisputeParty().has_object_permission(request, None, dispute):
            return Response(
                {'error': 'You are not authorized to comment on this dispute.'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = DisputeCommentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(dispute=dispute, author=request.user)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['patch'], permission_classes=[IsAdminUser])
    def set_under_review(self, request, pk=None):
        """
        Admin action to mark dispute as under review.
        """
        dispute = self.get_object()

        if dispute.status != 'open':
            return Response(
                {'error': 'Only open disputes can be set to under review.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        dispute.status = 'under_review'
        dispute.save(update_fields=['status'])

        return Response(DisputeSerializer(dispute).data)


class DisputeCommentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing dispute comments.
    """
    serializer_class = DisputeCommentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        dispute_id = self.kwargs.get('dispute_id')
        return DisputeComment.objects.filter(dispute_id=dispute_id)

    def perform_create(self, serializer):
        dispute_id = self.kwargs.get('dispute_id')
        dispute = Dispute.objects.get(pk=dispute_id)
        serializer.save(dispute=dispute, author=self.request.user)
