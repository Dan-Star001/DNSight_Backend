"""
Analytics — URL Configuration
================================
Audit log read-only endpoints via DRF router.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from analytics.views import AuditLogViewSet

router = DefaultRouter()
router.register(r'audit-logs', AuditLogViewSet, basename='audit-log')

urlpatterns = [
    path('', include(router.urls)),
]
