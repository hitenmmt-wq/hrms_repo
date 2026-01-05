"""
Custom permission classes for HRMS role-based access control.

Provides role-based permissions (Admin, HR, Employee) with appropriate
access levels for different user types across the HRMS system.
"""

from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsAdmin(BasePermission):
    """Admin permission: Read access for all authenticated users, write access for admins only."""

    def has_permission(self, request, view):
        """Allow read operations for authenticated users, write operations for admin role only."""
        if request.method in SAFE_METHODS:
            return request.user.is_authenticated
        return request.user.is_authenticated and request.user.role == "admin"


class IsHr(BasePermission):
    """HR permission: Read access for all authenticated users, write access for HR role only."""

    def has_permission(self, request, view):
        """Allow read operations for authenticated users, write operations for HR role only."""
        if request.method in SAFE_METHODS:
            return request.user.is_authenticated
        return request.user.is_authenticated and request.user.role == "hr"


class IsEmployee(BasePermission):
    """Employee permission: All operations allowed for employee role only."""

    def has_permission(self, request, view):
        """Allow all operations for authenticated users with employee role."""
        return request.user.is_authenticated and request.user.role == "employee"


class IsAuthenticated(BasePermission):
    """Basic authentication: All operations allowed for any authenticated user."""

    def has_permission(self, request, view):
        """Allow all operations for any authenticated user regardless of role."""
        return request.user.is_authenticated
