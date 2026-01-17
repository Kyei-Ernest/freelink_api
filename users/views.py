from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.contrib.auth import get_user_model, logout
from rest_framework.authtoken.models import Token
from .serializers import (UserSerializer, RegisterSerializer,
                          LoginSerializer, ChangePasswordSerializer,
                          ResetPasswordSerializer, VerifyEmailSerializer,
                          PasswordResetRequestSerializer )

from django.contrib.auth import update_session_auth_hash
from rest_framework import throttling

from django.core.mail import send_mail
from django.contrib.auth.tokens import PasswordResetTokenGenerator, default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
import logging

from wallet.models import Wallet
from notifications.models import Notification

from rest_framework import generics
from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiResponse

logger = logging.getLogger(__name__)
User = get_user_model()


@extend_schema(
    tags=['Authentication'],
    summary='Register a new user',
    description='''
    Create a new user account on the FREELINK platform.
    
    **User Types:**
    - `is_freelancer=true`: Register as a freelancer who can apply for jobs
    - `is_client=true`: Register as a client who can post jobs
    
    **Requirements:**
    - Valid email address (must be unique)
    - Password must be at least 8 characters
    - Phone number in international format (e.g., +233244123456)
    
    **Returns:** User details with authentication token
    ''',
    examples=[
        OpenApiExample(
            'Freelancer Registration',
            value={
                "email": "john@example.com",
                "password": "SecurePass123!",
                "password2": "SecurePass123!",
                "full_name": "John Doe",
                "phone": "+233244123456",
                "country": "Ghana",
                "is_freelancer": True,
                "is_client": False
            },
            request_only=True
        ),
        OpenApiExample(
            'Client Registration',
            value={
                "email": "jane@company.com",
                "password": "SecurePass123!",
                "password2": "SecurePass123!",
                "full_name": "Jane Smith",
                "phone": "+233244654321",
                "country": "Ghana",
                "is_freelancer": False,
                "is_client": True
            },
            request_only=True
        )
    ]
)
class RegisterView(generics.CreateAPIView):
    """Register a new user account."""
    queryset = User.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer


"""class ProfileView(generics.RetrieveUpdateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    def get(self, request, *args, **kwargs):
        user = self.get_object()
        serializer = self.get_serializer(user)
        return Response(serializer.data)

"""


@extend_schema(
    tags=['Authentication'],
    summary='Login to your account',
    description='''
    Authenticate with your email and password to receive an authentication token.
    
    **How to use the token:**
    Include it in the `Authorization` header of subsequent requests:
    ```
    Authorization: Token your_token_here
    ```
    
    **Returns:** Authentication token and user details
    ''',
    examples=[
        OpenApiExample(
            'Login Request',
            value={
                "email": "john@example.com",
                "password": "SecurePass123!"
            },
            request_only=True
        ),
        OpenApiExample(
            'Successful Login',
            value={
                "token": "a1b2c3d4e5f6g7h8i9j0...",
                "user": {
                    "id": 1,
                    "email": "john@example.com",
                    "full_name": "John Doe",
                    "is_freelancer": True,
                    "is_client": False
                }
            },
            response_only=True
        )
    ],
    responses={
        200: OpenApiResponse(description='Login successful'),
        400: OpenApiResponse(description='Invalid credentials')
    }
)
class LoginView(APIView):
    """Authenticate user and return auth token with user details."""
    serializer_class = LoginSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data
        token, created = Token.objects.get_or_create(user=user)
        user_data = UserSerializer(user).data
        return Response({"token": token.key, "user": user_data})


@extend_schema(
    tags=['Authentication'],
    summary='Logout from your account',
    description='''
    Log out the current user by invalidating their authentication token.
    
    **Note:** After logout, the token will no longer be valid and the user
    will need to login again to get a new token.
    ''',
    responses={
        200: OpenApiResponse(description='Logged out successfully'),
        401: OpenApiResponse(description='Authentication required')
    }
)
class LogoutView(APIView):
    """Log out user by deleting token and ending session."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        token = getattr(request.user, 'auth_token', None)
        if token:
            token.delete()
        logout(request)
        return Response({"detail": "Logged out successfully."}, status=status.HTTP_200_OK)


@extend_schema(
    tags=['Authentication'],
    summary='Change your password',
    description='''
    Change the password for the currently authenticated user.
    
    **Requirements:**
    - Must provide current (old) password
    - New password must be at least 8 characters
    - New password must match confirmation
    ''',
    examples=[
        OpenApiExample(
            'Change Password',
            value={
                "old_password": "CurrentPass123!",
                "new_password": "NewSecurePass456!",
                "confirm_password": "NewSecurePass456!"
            },
            request_only=True
        )
    ],
    responses={
        200: OpenApiResponse(description='Password updated successfully'),
        400: OpenApiResponse(description='Invalid current password or validation error')
    }
)
class ChangePasswordView(generics.UpdateAPIView):
    """Change password for the authenticated user."""
    serializer_class = ChangePasswordSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Password updated successfully."}, status=status.HTTP_200_OK)


class IsNotAuthenticated(permissions.BasePermission):
    """Permission that only allows unauthenticated users."""
    def has_permission(self, request, view):
        return not request.user.is_authenticated


class ResetPasswordView(APIView):
    """Reset password for unauthenticated users using uid and token."""
    serializer_class = ResetPasswordSerializer
    permission_classes = [IsNotAuthenticated]

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)

        if serializer.is_valid():
            try:
                uid = force_str(urlsafe_base64_decode(serializer.validated_data['uidb64']))
                user = User.objects.get(pk=uid)
            except (TypeError, ValueError, OverflowError, User.DoesNotExist):
                return Response(
                    {'error': 'Invalid user ID'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            new_password = serializer.validated_data['new_password']
            user.set_password(new_password)
            user.save()

            logger.info(
                f"Password reset for user: {user.username} "
                f"(Phone: {user.phone}, Role: {'Freelancer' if user.is_freelancer else 'Client'})"
            )

            return Response(
                {'message': f"Password reset successfully for {'freelancer' if user.is_freelancer else 'client'}"},
                status=status.HTTP_200_OK
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VerifyEmailView(APIView):
    """Verify email address for a newly registered user."""
    serializer_class = VerifyEmailSerializer
    permission_classes = []
    throttle_classes = [throttling.AnonRateThrottle]

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            user.is_verified = True
            user.save()

            logger.info(
                f"Email verified for user: {user.username} "
                f"(Phone: {user.phone}, Role: {'Freelancer' if user.is_freelancer else 'Client'})"
            )

            return Response(
                {'message': f"Email verified successfully for {'freelancer' if user.is_freelancer else 'client'}"},
                status=status.HTTP_200_OK
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


"""class VerifyPhoneView(APIView):
    serializer_class = VerifyPhoneSerializer
    permission_classes = [IsNotAuthenticated]
    throttle_classes = [throttling.AnonRateThrottle]

    def post(self, request):
        serializer = VerifyPhoneSerializer(data=request.data)
        if serializer.is_valid():
            try:
                user = User.objects.get(phone=serializer.validated_data['phone'])
            except User.DoesNotExist:
                return Response({'error': 'No user found with this phone number'}, status=status.HTTP_400_BAD_REQUEST)

            user.is_phone_verified = True
            user.save()



            cache.delete(f"phone_verification_{user.phone}")
            logger.info(
                f"Phone verified for user: {user.username} "
                f"(Phone: {user.phone}, Role: {'Freelancer' if user.is_freelancer else 'Client'})"
            )
            return Response(
                {'message': f"Phone verified successfully for {'freelancer' if user.is_freelancer else 'client'}"},
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
"""


class PasswordResetRequestView(generics.GenericAPIView):
    """Request a password reset link by providing email address."""
    serializer_class = PasswordResetRequestSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {"detail": "If an account exists, password reset instructions have been sent."},
                status=200
            )

        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))

        # Normally sent via email
        reset_link = f"http://frontend-site/reset-password/{uid}/{token}/"

        return Response({"reset_link": reset_link}, status=200)


"""class PasswordResetConfirmView(generics.GenericAPIView):
    ""Confirm password reset and set a new password using uid and token.""
    serializer_class = PasswordResetConfirmSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Password has been reset successfully."}, status=200)

"""

"""class SendVerificationEmailView(APIView):
    serializer_class = SendVerificationEmailSerializer
    permission_classes = [IsNotAuthenticated]
    throttle_classes = [throttling.AnonRateThrottle]

    def post(self, request):
        email = request.data.get('email')
        try:
            user = User.objects.get(email=email, is_verified=False)
        except User.DoesNotExist:
            return Response(
                {'message': 'If an unverified account exists, a verification link will be sent'},
                status=status.HTTP_200_OK
            )

        token = PasswordResetTokenGenerator().make_token(user)
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        verify_url = f"{request.scheme}://{request.get_host()}/verify-email/?uidb64={uidb64}&token={token}"

        send_mail(
            subject='Verify Your Email',
            message=f'Click the link to verify your email: {verify_url}',
            from_email='kookyei44@gmail.com',
            recipient_list=[user.email],
        )

        logger.info(f"Verification email sent to {user.email} (Phone: {user.phone})")
        return Response(
            {'message': 'If an unverified account exists, a verification link will be sent'},
            status=status.HTTP_200_OK
        )
"""