from django.contrib import admin
from .models import Job, Skill, SkillBadge, UserSkillBadge


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ('title', 'client', 'status', 'budget', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('title', 'description', 'client__email')
    ordering = ['-created_at']


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'is_popular', 'badge_count')
    list_filter = ('category', 'is_popular')
    search_fields = ('name',)
    ordering = ['name']

    def badge_count(self, obj):
        return obj.badges.filter(is_active=True).count()
    badge_count.short_description = 'Active Badges'


@admin.register(SkillBadge)
class SkillBadgeAdmin(admin.ModelAdmin):
    list_display = ('name', 'skill', 'level', 'verification_method', 'is_active', 'holder_count')
    list_filter = ('level', 'verification_method', 'is_active', 'skill')
    search_fields = ('name', 'skill__name')
    ordering = ['skill__name', 'level']

    def holder_count(self, obj):
        return obj.holders.filter(status='verified').count()
    holder_count.short_description = 'Verified Holders'


@admin.register(UserSkillBadge)
class UserSkillBadgeAdmin(admin.ModelAdmin):
    list_display = ('user', 'badge', 'status', 'score', 'earned_at', 'verified_at')
    list_filter = ('status', 'badge__skill', 'badge__level')
    search_fields = ('user__email', 'badge__name')
    ordering = ['-earned_at']
    readonly_fields = ('earned_at',)

    actions = ['verify_badges', 'revoke_badges']

    def verify_badges(self, request, queryset):
        from django.utils import timezone
        count = queryset.filter(status='pending').update(
            status='verified',
            verified_by=request.user,
            verified_at=timezone.now()
        )
        self.message_user(request, f'{count} badge(s) verified.')
    verify_badges.short_description = 'Verify selected badges'

    def revoke_badges(self, request, queryset):
        count = queryset.exclude(status='revoked').update(status='revoked')
        self.message_user(request, f'{count} badge(s) revoked.')
    revoke_badges.short_description = 'Revoke selected badges'
