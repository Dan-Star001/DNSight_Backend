"""Analytics — Django Admin Configuration"""

from django.contrib import admin

from analytics.models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'hospital', 'user', 'action', 'ip_address', 'created_at')
    list_filter = ('action', 'hospital')
    search_fields = ('action', 'user__email')
    readonly_fields = ('hospital', 'user', 'action', 'ip_address', 'details', 'created_at')
