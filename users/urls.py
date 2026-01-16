from django.urls import path
from .views import (
    RegisterView, LoginView, LogoutView,  # ProfileView,
    VerifyEmailView,  # VerifyPhoneView,
    ChangePasswordView, ResetPasswordView, PasswordResetRequestView,
    # PasswordResetConfirmView,  # SendVerificationEmailView
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
   # path('profile/', ProfileView.as_view(), name='profile'),
    path('verify-email/', VerifyEmailView.as_view(), name='verify-email'),
   # path('verify-phone/', VerifyPhoneView.as_view(), name='verify-phone'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset-password'),
    path('password-reset-request/', PasswordResetRequestView.as_view(), name='password-reset-request'),
   # path('password-reset/confirm/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),

    # path('send-verification-email/', SendVerificationEmailView.as_view(), name='send-verification-email'),
]