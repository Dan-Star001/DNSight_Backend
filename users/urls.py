"""
Users — URL Configuration
============================
Authentication and user profile endpoints.
"""

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from users.views import (
    AdminRegistrationView,
    CustomTokenObtainPairView,
    DoctorRegistrationView,
    UserProfileView,
)

urlpatterns = [
    path('auth/admin/register/', AdminRegistrationView.as_view(), name='admin-register'),
    path('auth/doctor/register/', DoctorRegistrationView.as_view(), name='doctor-register'),
    path('auth/token/', CustomTokenObtainPairView.as_view(), name='token-obtain'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('users/me/', UserProfileView.as_view(), name='user-profile'),
]
