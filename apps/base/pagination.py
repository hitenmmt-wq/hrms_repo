"""
Custom pagination classes for HRMS API responses.

Provides standardized pagination with configurable page sizes
for consistent API response formatting across all endpoints.
"""

from rest_framework.pagination import PageNumberPagination


class CustomPageNumberPagination(PageNumberPagination):
    """Custom pagination with configurable page size and maximum limits."""

    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100
