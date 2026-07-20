"""
Users — Custom DRF Permissions
=================================
Granular, role-based permission classes that complement DRF's built-in
``IsAuthenticated`` to enforce RBAC across the API surface.
"""

from rest_framework.permissions import BasePermission


class IsActiveUser(BasePermission):
    """Allows access only to users whose account status is ACTIVE.
    This prevents PENDING or REJECTED users from accessing protected endpoints
    even if they hold a valid JWT token."""

    message = 'Your account is not yet active. Please wait for admin approval.'

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.status == 'ACTIVE'
        )


class IsAdmin(BasePermission):
    """Restricts access to hospital administrators only."""

    message = 'Administrator privileges are required for this action.'

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == 'ADMIN'
            and request.user.status == 'ACTIVE'
        )


class IsDoctor(BasePermission):
    """Restricts access to active doctors only."""

    message = 'Doctor privileges are required for this action.'

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == 'DOCTOR'
            and request.user.status == 'ACTIVE'
        )
