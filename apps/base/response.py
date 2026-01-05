"""
Standardized API response utilities for consistent response formatting.

Provides uniform success and error response structures across all
HRMS API endpoints for better client-side handling.
"""

from rest_framework.response import Response


class ApiResponse:
    """Utility class for creating standardized API responses."""

    @staticmethod
    def success(message: str, data=None, status=200):
        """Create standardized success response with optional data payload."""
        return Response(
            {"success": True, "message": message, "data": data}, status=status
        )

    @staticmethod
    def error(message: str, errors=None, status=400):
        """Create standardized error response with optional error details."""
        return Response(
            {"success": False, "message": message, "errors": errors}, status=status
        )
