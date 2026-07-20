"""
Analytics — DRF Serializers
==============================
Read-only serializer for audit log entries.
"""

from rest_framework import serializers

from analytics.models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    """Read-only serializer for audit log entries."""

    user_email = serializers.CharField(source='user.email', read_only=True, default=None)

    class Meta:
        model = AuditLog
        fields = [
            'id', 'hospital', 'user', 'user_email',
            'action', 'ip_address', 'details', 'created_at',
        ]
        read_only_fields = fields
