from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Profile

User = get_user_model()


class ProfileSerializer(serializers.ModelSerializer):
    """Serializer for viewing own profile with all details."""
    user_id = serializers.ReadOnlyField(source='user.id')
    email = serializers.ReadOnlyField(source='user.email')
    full_name = serializers.ReadOnlyField(source='user.full_name')
    phone = serializers.ReadOnlyField(source='user.phone')
    country = serializers.ReadOnlyField(source='user.country')
    language_preference = serializers.ReadOnlyField(source='user.language_preference')
    is_freelancer = serializers.ReadOnlyField(source='user.is_freelancer')
    is_client = serializers.ReadOnlyField(source='user.is_client')
    is_verified = serializers.ReadOnlyField(source='user.is_verified')
    is_phone_verified = serializers.ReadOnlyField(source='user.is_phone_verified')

    # Stats fields
    response_time = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    jobs_completed = serializers.SerializerMethodField()
    on_time_rate = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = [
            'user_id',
            'email',
            'full_name',
            'phone',
            'country',
            'language_preference',
            'is_freelancer',
            'is_client',
            'bio',
            'skills',
            'hourly_rate',
            'experience_years',
            'company_name',
            'company_description',
            'location',
            'website',
            'profile_picture',
            'is_verified',
            'is_phone_verified',
            'response_time',
            'average_rating',
            'jobs_completed',
            'on_time_rate',
            'created_at',
            'updated_at',
        ]
        read_only_fields = fields

    def get_response_time(self, obj):
        if hasattr(obj.user, 'stats'):
            return obj.user.stats.response_time_display
        return "No data"

    def get_average_rating(self, obj):
        if hasattr(obj.user, 'stats'):
            return str(obj.user.stats.average_rating)
        return "0.00"

    def get_jobs_completed(self, obj):
        if hasattr(obj.user, 'stats'):
            return obj.user.stats.jobs_completed
        return 0

    def get_on_time_rate(self, obj):
        if hasattr(obj.user, 'stats'):
            return f"{obj.user.stats.on_time_delivery_rate}%"
        return "100%"


class ProfileUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating profile."""
    full_name = serializers.CharField(source='user.full_name', required=False)
    phone = serializers.CharField(source='user.phone', required=False)
    language_preference = serializers.CharField(source='user.language_preference', required=False)

    class Meta:
        model = Profile
        fields = [
            'full_name',
            'phone',
            'language_preference',
            'bio',
            'skills',
            'hourly_rate',
            'experience_years',
            'company_name',
            'company_description',
            'location',
            'website',
            'profile_picture'
        ]

    def update(self, instance, validated_data):
        # Handle user fields separately
        user_data = validated_data.pop('user', {})
        for attr, value in user_data.items():
            setattr(instance.user, attr, value)
        instance.user.save()

        # Update profile fields
        return super().update(instance, validated_data)


class PublicProfileSerializer(serializers.ModelSerializer):
    """Serializer for viewing other users' public profiles."""
    full_name = serializers.ReadOnlyField(source='user.full_name')
    is_freelancer = serializers.ReadOnlyField(source='user.is_freelancer')
    is_client = serializers.ReadOnlyField(source='user.is_client')
    response_time = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = [
            'full_name',
            'is_freelancer',
            'is_client',
            'bio',
            'skills',
            'hourly_rate',
            'experience_years',
            'company_name',
            'location',
            'website',
            'profile_picture',
            'response_time',
            'average_rating',
        ]

    def get_response_time(self, obj):
        if hasattr(obj.user, 'stats'):
            return obj.user.stats.response_time_display
        return "No data"

    def get_average_rating(self, obj):
        if hasattr(obj.user, 'stats'):
            return str(obj.user.stats.average_rating)
        return "0.00"


class UserStatsSerializer(serializers.ModelSerializer):
    """Serializer for user performance stats."""
    response_time_display = serializers.CharField(read_only=True)

    class Meta:
        from .models import UserStats
        model = UserStats
        fields = [
            'total_messages_received',
            'average_response_time_seconds',
            'response_time_display',
            'jobs_completed',
            'jobs_on_time',
            'on_time_delivery_rate',
            'total_ratings',
            'average_rating',
            'last_online',
        ]


class ReferralSerializer(serializers.ModelSerializer):
    """Serializer for referral display."""
    referrer_name = serializers.CharField(source='referrer.full_name', read_only=True)
    referred_user_name = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        from .models import Referral
        model = Referral
        fields = [
            'id',
            'referrer',
            'referrer_name',
            'referred_email',
            'referred_user',
            'referred_user_name',
            'referral_code',
            'status',
            'status_display',
            'reward_amount',
            'created_at',
            'registered_at',
            'rewarded_at',
        ]
        read_only_fields = [
            'id', 'referrer', 'referral_code', 'status',
            'created_at', 'registered_at', 'rewarded_at'
        ]

    def get_referred_user_name(self, obj):
        if obj.referred_user:
            return obj.referred_user.full_name
        return None


class ReferralCreateSerializer(serializers.Serializer):
    """Serializer for creating a referral invitation."""
    email = serializers.EmailField()
