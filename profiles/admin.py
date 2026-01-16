from django.contrib import admin
from .models import Profile, UserStats, Referral


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'location', 'hourly_rate', 'experience_years', 'created_at')
    list_filter = ('user__is_freelancer', 'user__is_client', 'created_at')
    search_fields = ('user__email', 'user__full_name', 'bio')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(UserStats)
class UserStatsAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'response_time_display', 'average_rating',
        'jobs_completed', 'on_time_delivery_rate', 'last_online'
    )
    list_filter = ('updated_at',)
    search_fields = ('user__email', 'user__full_name')
    readonly_fields = ('updated_at',)

    def response_time_display(self, obj):
        return obj.response_time_display
    response_time_display.short_description = 'Avg Response Time'


@admin.register(Referral)
class ReferralAdmin(admin.ModelAdmin):
    list_display = (
        'referrer', 'referred_email', 'status',
        'reward_amount', 'created_at', 'registered_at'
    )
    list_filter = ('status', 'created_at')
    search_fields = ('referrer__email', 'referred_email', 'referral_code')
    readonly_fields = ('created_at',)
