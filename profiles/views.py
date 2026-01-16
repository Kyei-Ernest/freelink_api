from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.utils import timezone
import secrets
import string

from .models import Profile, UserStats, Referral
from .serializers import (
    ProfileSerializer,
    ProfileUpdateSerializer,
    PublicProfileSerializer,
    ReferralSerializer,
    ReferralCreateSerializer,
    UserStatsSerializer,
)

User = get_user_model()


class MyProfileView(generics.RetrieveAPIView):
    """GET /profile/me/ → View your own profile with stats."""
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        # Ensure stats exist
        UserStats.objects.get_or_create(user=self.request.user)
        return self.request.user.profile


class MyProfileUpdateView(generics.UpdateAPIView):
    """PATCH /profile/me/update/ → Update your own profile."""
    serializer_class = ProfileUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user.profile


class PublicProfileView(generics.RetrieveAPIView):
    """GET /profile/<email>/ → View a public profile."""
    serializer_class = PublicProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'user__email'

    def get_queryset(self):
        return Profile.objects.select_related('user').all()


class MyStatsView(generics.RetrieveAPIView):
    """GET /profile/stats/ → View your performance stats."""
    serializer_class = UserStatsSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        stats, _ = UserStats.objects.get_or_create(user=self.request.user)
        return stats


# ============== Referral System ==============

def generate_referral_code():
    """Generate a unique 8-character referral code."""
    chars = string.ascii_uppercase + string.digits
    while True:
        code = ''.join(secrets.choice(chars) for _ in range(8))
        if not Referral.objects.filter(referral_code=code).exists():
            return code


class MyReferralCodeView(APIView):
    """GET /profile/referral/code/ → Get or create your referral code."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # Check if user has an existing referral they made
        existing = Referral.objects.filter(referrer=request.user).first()
        if existing:
            code = existing.referral_code
        else:
            code = generate_referral_code()

        return Response({
            'referral_code': code,
            'referral_link': f"https://freelink.com/register?ref={code}",
            'referrals_count': Referral.objects.filter(referrer=request.user).count(),
            'successful_referrals': Referral.objects.filter(
                referrer=request.user,
                status__in=['completed', 'rewarded']
            ).count(),
        })


class CreateReferralView(APIView):
    """POST /profile/referral/ → Invite someone via email."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({'error': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)

        # Check if email already registered
        if User.objects.filter(email=email).exists():
            return Response(
                {'error': 'This email is already registered'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if already referred
        if Referral.objects.filter(referred_email=email).exists():
            return Response(
                {'error': 'This email has already been referred'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create referral
        referral = Referral.objects.create(
            referrer=request.user,
            referred_email=email,
            referral_code=generate_referral_code(),
        )

        # TODO: Send email invitation here

        return Response(ReferralSerializer(referral).data, status=status.HTTP_201_CREATED)


class MyReferralsView(generics.ListAPIView):
    """GET /profile/referrals/ → List all your referrals."""
    serializer_class = ReferralSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Referral.objects.filter(referrer=self.request.user).order_by('-created_at')


class ValidateReferralCodeView(APIView):
    """GET /profile/referral/validate/<code>/ → Validate a referral code."""
    permission_classes = [permissions.AllowAny]

    def get(self, request, code):
        try:
            referral = Referral.objects.get(referral_code=code)
            if referral.status != 'pending':
                return Response(
                    {'valid': False, 'error': 'This referral code has already been used'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            return Response({
                'valid': True,
                'referrer_name': referral.referrer.full_name,
            })
        except Referral.DoesNotExist:
            return Response(
                {'valid': False, 'error': 'Invalid referral code'},
                status=status.HTTP_404_NOT_FOUND
            )


class ApplyReferralCodeView(APIView):
    """POST /profile/referral/apply/ → Apply referral code after registration."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        code = request.data.get('referral_code')
        if not code:
            return Response({'error': 'Referral code is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            referral = Referral.objects.get(referral_code=code, status='pending')
        except Referral.DoesNotExist:
            return Response({'error': 'Invalid or used referral code'}, status=status.HTTP_404_NOT_FOUND)

        # Check if user is already referred
        if hasattr(request.user, 'referred_by'):
            return Response({'error': 'You have already used a referral code'}, status=status.HTTP_400_BAD_REQUEST)

        # Apply referral
        referral.referred_user = request.user
        referral.status = 'registered'
        referral.registered_at = timezone.now()
        referral.save()

        return Response({
            'message': 'Referral code applied successfully!',
            'referrer': referral.referrer.full_name,
        })
