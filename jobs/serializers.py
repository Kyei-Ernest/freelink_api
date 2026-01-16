from rest_framework import serializers
from .models import Job, Skill, SkillBadge, UserSkillBadge


class SkillSerializer(serializers.ModelSerializer):
    """Serializer for Skill model."""
    badge_count = serializers.SerializerMethodField()

    class Meta:
        model = Skill
        fields = ["id", "name", "category", "description", "icon", "is_popular", "badge_count"]
        read_only_fields = ["id"]

    def get_badge_count(self, obj):
        return obj.badges.filter(is_active=True).count()

    def validate_name(self, value):
        normalized = value.strip().title()
        if self.instance:
            # Update case - exclude current instance
            if Skill.objects.filter(name__iexact=normalized).exclude(pk=self.instance.pk).exists():
                raise serializers.ValidationError("This skill already exists.")
        else:
            # Create case
            if Skill.objects.filter(name__iexact=normalized).exists():
                raise serializers.ValidationError("This skill already exists.")
        return normalized


class SkillBadgeSerializer(serializers.ModelSerializer):
    """Serializer for skill badges."""
    skill_name = serializers.CharField(source='skill.name', read_only=True)
    level_display = serializers.CharField(source='get_level_display', read_only=True)
    verification_method_display = serializers.CharField(source='get_verification_method_display', read_only=True)
    holder_count = serializers.SerializerMethodField()

    class Meta:
        model = SkillBadge
        fields = [
            'id', 'skill', 'skill_name', 'level', 'level_display',
            'name', 'description', 'icon_color', 'verification_method',
            'verification_method_display', 'passing_score', 'is_active',
            'holder_count', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

    def get_holder_count(self, obj):
        return obj.holders.filter(status='verified').count()


class UserSkillBadgeSerializer(serializers.ModelSerializer):
    """Serializer for user's earned badges."""
    badge_name = serializers.CharField(source='badge.name', read_only=True)
    skill_name = serializers.CharField(source='badge.skill.name', read_only=True)
    level = serializers.CharField(source='badge.level', read_only=True)
    level_display = serializers.CharField(source='badge.get_level_display', read_only=True)
    icon_color = serializers.CharField(source='badge.icon_color', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    is_valid = serializers.BooleanField(read_only=True)

    class Meta:
        model = UserSkillBadge
        fields = [
            'id', 'user', 'badge', 'badge_name', 'skill_name',
            'level', 'level_display', 'icon_color', 'status', 'status_display',
            'score', 'certificate_url', 'is_valid', 'earned_at', 'expires_at', 'verified_at'
        ]
        read_only_fields = ['id', 'user', 'status', 'verified_at', 'earned_at']


class UserSkillBadgeCreateSerializer(serializers.ModelSerializer):
    """Serializer for applying for a badge."""

    class Meta:
        model = UserSkillBadge
        fields = ['badge', 'certificate_url']

    def validate_badge(self, value):
        if not value.is_active:
            raise serializers.ValidationError("This badge is not available.")
        return value

    def validate(self, data):
        user = self.context['request'].user
        badge = data['badge']
        if UserSkillBadge.objects.filter(user=user, badge=badge).exists():
            raise serializers.ValidationError("You have already applied for this badge.")
        return data


class UserSkillBadgeVerifySerializer(serializers.Serializer):
    """Serializer for admin badge verification."""
    status = serializers.ChoiceField(choices=['verified', 'revoked'])
    score = serializers.IntegerField(required=False, min_value=0, max_value=100)


# Job Serializers
class JobSerializer(serializers.ModelSerializer):
    """Serializer for creating and listing jobs."""
    client = serializers.StringRelatedField(read_only=True)
    freelancer = serializers.StringRelatedField(read_only=True)
    skills_required = serializers.SlugRelatedField(
        many=True,
        slug_field="name",
        queryset=Skill.objects.all(),
        required=False
    )

    class Meta:
        model = Job
        fields = '__all__'
        read_only_fields = ('client', 'freelancer', 'status', 'created_at', 'updated_at')

    def create(self, validated_data):
        skills = validated_data.pop("skills_required", [])
        job = Job.objects.create(**validated_data)

        for skill in skills:
            job.skills_required.add(skill)

        return job


class JobDetailSerializer(JobSerializer):
    """Detailed serializer for a single job with related info."""
    client = serializers.StringRelatedField(read_only=True)
    freelancer = serializers.StringRelatedField(read_only=True)
    proposal_count = serializers.SerializerMethodField()

    class Meta(JobSerializer.Meta):
        pass

    def get_proposal_count(self, obj):
        return obj.proposals_received.count()


class JobStatusSerializer(serializers.ModelSerializer):
    """Serializer for updating only the job status."""

    class Meta:
        model = Job
        fields = ('status',)
