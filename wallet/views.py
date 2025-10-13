from rest_framework.exceptions import ValidationError
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, viewsets, permissions
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import UserRateThrottle
from .models import Wallet, Currency
from .serializers import CurrencySerializer,WalletSerializer

import logging


logger = logging.getLogger(__name__)


class WalletView(APIView):
    """
    Retrieve the authenticated user's wallet.

    Only verified clients or freelancers can access this endpoint.
    """
    serializer_class = WalletSerializer
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]

    def get(self, request):
        """
        GET: Return wallet details (balance, currency, available balance).

        - 200 OK: Wallet found
        - 403 Forbidden: Not client/freelancer or not verified
        - 404 Not Found: Wallet missing
        """
        if not (request.user.is_client or request.user.is_freelancer):
            return Response(
                {'error': 'Only profiles or freelancers can access their wallet'},
                status=status.HTTP_403_FORBIDDEN
            )
        if not request.user.is_verified:
            return Response(
                {'error': 'Account must be verified to access wallet'},
                status=status.HTTP_403_FORBIDDEN
            )
        try:
            wallet = request.user.wallet
            serializer = WalletSerializer(wallet)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Wallet.DoesNotExist:
            return Response(
                {'error': 'Wallet not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class IsAdminUser(permissions.BasePermission):
    """Allow access only to admin (staff) users."""

    def has_permission(self, request, view):
        return request.user and request.user.is_staff


class CurrencyViewSet(viewsets.ModelViewSet):
    """
    Manage currencies (CRUD).

    Restricted to admin users only.
    """
    queryset = Currency.objects.all()
    serializer_class = CurrencySerializer
    permission_classes = [IsAdminUser]

