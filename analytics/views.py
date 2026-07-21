"""
Analytics — DRF Views
========================
Read-only audit log viewer restricted to hospital admins.
"""

from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from analytics.models import AuditLog
from analytics.serializers import AuditLogSerializer
from users.permissions import IsAdmin


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """GET /api/audit-logs/

    Read-only, paginated access to audit logs. Restricted to hospital admins.
    """

    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated, IsAdmin]

    def get_queryset(self):
        return (
            AuditLog.objects
            .filter(hospital_id=self.request.user.hospital_id)
            .select_related('user')
            .only(
                'id', 'action', 'ip_address', 'details', 'created_at',
                'hospital_id', 'user__id', 'user__email',
            )
        )

    @method_decorator(cache_page(60))
    def list(self, request, *args, **kwargs):
        """Cached report page (60 seconds)."""
        return super().list(request, *args, **kwargs)

    @method_decorator(cache_page(60))
    def retrieve(self, request, *args, **kwargs):
        """Cached report profile modal (60 seconds)."""
        return super().retrieve(request, *args, **kwargs)
