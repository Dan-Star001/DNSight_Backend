"""
Analytics — Django ORM Models
===============================
Immutable audit log entries for compliance and event tracking.
"""

from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    """Immutable log entry capturing administrative and clinical events with
    full context for compliance and auditing."""

    id = models.BigAutoField(primary_key=True)
    hospital = models.ForeignKey(
        'hospitals.Hospital',
        on_delete=models.CASCADE,
        related_name='audit_logs',
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs',
    )
    action = models.CharField(max_length=255)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    details = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'[{self.created_at}] {self.action} by {self.user}'
