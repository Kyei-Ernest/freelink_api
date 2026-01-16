from django.contrib.auth import authenticate, get_user_model
from rest_framework import serializers

from django.contrib.auth.tokens import PasswordResetTokenGenerator, default_token_generator
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str

from wallet.models import Wallet
from notifications.models import Notification


User = get_user_model()

"""class WalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields = ['balance']
"""


"""class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'title', 'message', 'is_read', 'created_at']
"""


class VerifyEmailSerializer(serializers.Serializer):
    token = serializers.CharField(required=True, write_only=True)
    uidb64 = serializers.CharField(required=True, write_only=True)

    def validate(self, data):
        try:
            uid = force_str(urlsafe_base64_decode(data['uidb64']))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            raise serializers.ValidationError({'uidb64': 'Invalid user ID'})
        token_generator = PasswordResetTokenGenerator()
        if not token_generator.check_token(user, data['token']):
            raise serializers.ValidationError({'token': 'Invalid or expired token'})
        if user.is_verified:
            raise serializers.ValidationError({'error': 'Email is already verified'})
        
        data['user'] = user

        return data


class UserSerializer(serializers.ModelSerializer):
   # wallet = WalletSerializer(read_only=True)
   # notifications = serializers.SerializerMethodField()
    #unread_messages = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id',
            'full_name',
            'email',
            'phone',
            'country',
            'is_freelancer',
            'is_client',
            'language_preference',
            'is_verified',
            'is_phone_verified',
        ]

    def get_notifications(self, obj):
        return Notification.objects.filter(user=obj, is_read=False).count()

    """def get_unread_messages(self, obj):
        return Message.objects.filter(recipient=obj, is_read=False).count()"""


class RegisterSerializer(serializers.ModelSerializer):
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = (
            'full_name', 'email', 'phone', 'country', 'password', 'password_confirm',
            'is_freelancer', 'is_client'
        )
        extra_kwargs = {
            'password': {'write_only': True},
            'email': {'required': True},
            'full_name': {'required': True},
            'phone': {'required': True}
        }

    def validate(self, data):
        # Password confirmation check
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({"password_confirm": "Passwords do not match."})

        # Role validation
        if data.get('is_freelancer') and data.get('is_client'):
            raise serializers.ValidationError("A user cannot be both a freelancer and a client.")
        if not data.get('is_freelancer') and not data.get('is_client'):
            raise serializers.ValidationError("User must be either a freelancer or a client.")

        return data

    def create(self, validated_data):
        validated_data.pop('password_confirm')  # Remove confirm field before saving

        user = User.objects.create_user(
            full_name=validated_data['full_name'],
            email=validated_data['email'],
            phone=validated_data['phone'],
            password=validated_data['password'],
            is_freelancer=validated_data.get('is_freelancer', False),
            is_client=validated_data.get('is_client', False),
        )
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(**data)
        if user and user.is_active:
            return user
        raise serializers.ValidationError("Invalid credentials")


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True)
    confirm_password = serializers.CharField(required=True, write_only=True)

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is not correct.")
        return value

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "New passwords must match."})

        if attrs['new_password'] == attrs['old_password']:
            raise serializers.ValidationError({"new_password": "New password cannot be the same as the old password."})

        return attrs

    def save(self, **kwargs):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class ResetPasswordSerializer(serializers.Serializer):
    token = serializers.CharField(required=True, write_only=True)
    uidb64 = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True)
    confirm_new_password = serializers.CharField(required=True, write_only=True)

    def validate(self, data):
        # Check if new passwords match
        if data['new_password'] != data['confirm_new_password']:
            raise serializers.ValidationError({'confirm_new_password': 'New passwords do not match'})

        # Check minimum password length
        if len(data['new_password']) < 8:
            raise serializers.ValidationError({'new_password': 'New password must be at least 8 characters long'})

        # Validate token and user
        try:
            uid = force_str(urlsafe_base64_decode(data['uidb64']))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            raise serializers.ValidationError({'uidb64': 'Invalid user ID'})

        token_generator = PasswordResetTokenGenerator()
        if not token_generator.check_token(user, data['token']):
            raise serializers.ValidationError({'token': 'Invalid or expired token'})

        return data


"""class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "Passwords must match."})
        return attrs

    def save(self, **kwargs):
        uid = self.validated_data['uid']
        token = self.validated_data['token']
        new_password = self.validated_data['new_password']

        try:
            uid_decoded = urlsafe_base64_decode(uid).decode()
            user = User.objects.get(pk=uid_decoded)
        except (User.DoesNotExist, ValueError, TypeError):
            raise serializers.ValidationError({"uid": "Invalid reset link."})

        if not default_token_generator.check_token(user, token):
            raise serializers.ValidationError({"token": "Invalid or expired token."})

        user.set_password(new_password)
        user.save()
        return user
"""
"""class VerifyPhoneSerializer(serializers.Serializer):
    phone = serializers.CharField(required=True, write_only=True)
    code = serializers.CharField(required=True, write_only=True)

    def validate(self, data):
        try:
            user = User.objects.get(phone=data['phone'])
        except User.DoesNotExist:
            raise serializers.ValidationError({'phone': 'No user found with this phone number'})
        if user.is_verified:
            raise serializers.ValidationError({'phone': 'Phone number is already verified'})
        cached_code = cache.get(f"phone_verification_{user.phone}")
        if not cached_code or cached_code != data['code']:
            raise serializers.ValidationError({'code': 'Invalid or expired verification code'})
        return data
"""


"""class SendVerificationEmailSerializer(serializers.Serializer):
    email = serializers.EmailField()
"""


class EmptySerializer(serializers.Serializer):
    """Serializer for endpoints that don't require input."""
    pass

