"""
Analytics — Audit Logging Helpers
====================================
Provides a reusable utility for recording administrative and clinical events
into the AuditLog table. Called explicitly from views across all apps.
"""

from analytics.models import AuditLog


def get_client_ip(request) -> str | None:
    """Extract the real client IP address from the request, handling
    reverse proxies that set the ``X-Forwarded-For`` header."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def log_action(request, action: str, details: dict | None = None) -> AuditLog:
    """Create an AuditLog entry tied to the current user and hospital.

    This function is intentionally *not* a middleware — it is called explicitly
    from view logic so that only meaningful events are recorded with the right
    context, avoiding noise from read-only requests.

    Args:
        request:  The DRF request object (must have an authenticated user).
        action:   A short, human-readable description of the event.
        details:  Optional dict of extra context to persist in the JSONField.

    Returns:
        The created AuditLog instance.
    """
    user = request.user if request.user.is_authenticated else None
    hospital_id = getattr(user, 'hospital_id', None)

    return AuditLog.objects.create(
        hospital_id=hospital_id,
        user=user,
        action=action,
        ip_address=get_client_ip(request),
        details=details or {},
    )
