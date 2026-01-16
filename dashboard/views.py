from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import UserRateThrottle
from .models import Dashboard
import logging

from .serializers import DashboardSerializer

logger = logging.getLogger(__name__)



class DashboardView(APIView):
    serializer_class = DashboardSerializer
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]

    def get(self, request):
        if not (request.user.is_client or request.user.is_freelancer):
            return Response(
                {'error': 'Only profiles or freelancers can access their dashboard'},
                status=status.HTTP_403_FORBIDDEN
            )
        if not request.user.is_verified:
            return Response(
                {'error': 'Account must be verified to access dashboard'},
                status=status.HTTP_403_FORBIDDEN
            )
        try:
            dashboard = request.user.dashboard
            # Update metrics before returning
            dashboard.update_metrics()
            serializer = DashboardSerializer(dashboard)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Dashboard.DoesNotExist:
            return Response(
                {'error': 'Dashboard not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    def post(self, request):
        if not (request.user.is_client or request.user.is_freelancer):
            return Response(
                {'error': 'Only profiles or freelancers can create a dashboard'},
                status=status.HTTP_403_FORBIDDEN
            )
        if not request.user.is_verified:
            return Response(
                {'error': 'Account must be verified to create a dashboard'},
                status=status.HTTP_403_FORBIDDEN
            )
        if hasattr(request.user, 'dashboard'):
            return Response(
                {'error': 'Dashboard already exists'},
                status=status.HTTP_400_BAD_REQUEST
            )
        serializer = DashboardSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            logger.info(
                f"Dashboard created for user: {request.user.email} "
                f"(Phone: {request.user.phone}, Role: {'Freelancer' if request.user.is_freelancer else 'Client'})"
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        if not (request.user.is_client or request.user.is_freelancer):
            return Response(
                {'error': 'Only profiles or freelancers can update their dashboard'},
                status=status.HTTP_403_FORBIDDEN
            )
        if not request.user.is_verified:
            return Response(
                {'error': 'Account must be verified to update dashboard'},
                status=status.HTTP_403_FORBIDDEN
            )
        try:
            dashboard = request.user.dashboard
        except Dashboard.DoesNotExist:
            return Response(
                {'error': 'Dashboard not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = DashboardSerializer(dashboard, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            # Optionally update metrics after preferences change
            dashboard.update_metrics()
            logger.info(
                f"Dashboard updated for user: {request.user.email} "
                f"(Phone: {request.user.phone}, Role: {'Freelancer' if request.user.is_freelancer else 'Client'})"
            )
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)