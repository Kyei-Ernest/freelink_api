from django.urls import path
from .views import (
    MyProfileView,
    MyProfileUpdateView,
    PublicProfileView,
    MyStatsView,
    MyReferralCodeView,
    CreateReferralView,
    MyReferralsView,
    ValidateReferralCodeView,
    ApplyReferralCodeView,
)

urlpatterns = [
    # Profile endpoints
    path('me/', MyProfileView.as_view(), name='my-profile'),
    path('me/update/', MyProfileUpdateView.as_view(), name='update-profile'),
    path('stats/', MyStatsView.as_view(), name='my-stats'),
    path('user/<user__email>/', PublicProfileView.as_view(), name='public-profile'),

    # Referral endpoints
    path('referral/code/', MyReferralCodeView.as_view(), name='my-referral-code'),
    path('referral/', CreateReferralView.as_view(), name='create-referral'),
    path('referrals/', MyReferralsView.as_view(), name='my-referrals'),
    path('referral/validate/<str:code>/', ValidateReferralCodeView.as_view(), name='validate-referral'),
    path('referral/apply/', ApplyReferralCodeView.as_view(), name='apply-referral'),
]
