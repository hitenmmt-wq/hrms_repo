"""
Base ViewSet with standardized CRUD operations and soft delete support.

Provides common ViewSet functionality with consistent API responses
and soft delete operations for all HRMS model ViewSets.
"""

from rest_framework import status, viewsets
from rest_framework.decorators import action

from apps.base.response import ApiResponse


class BaseViewSet(viewsets.ModelViewSet):
    """Base ViewSet with standardized responses and soft delete operations."""

    entity_name: str = None

    def create(self, request, *args, **kwargs):
        """Create new entity with standardized success response."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        return ApiResponse.success(
            message=f"{self.entity_name} created successfully",
            data=serializer.data,
            status=status.HTTP_201_CREATED,
        )

    def update(self, request, *args, **kwargs):
        """Update existing entity with standardized success response."""
        partial = kwargs.pop("partial", False)
        instance = self.get_object()

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return ApiResponse.success(
            message=f"{self.entity_name} updated successfully",
            data=serializer.data,
            status=status.HTTP_200_OK,
        )

    def destroy(self, request, *args, **kwargs):
        """Soft delete entity if supported, otherwise hard delete."""
        instance = self.get_object()
        if hasattr(instance, "soft_delete"):
            instance.soft_delete()
        else:
            instance.delete()

        return ApiResponse.success(
            message=f"{self.entity_name} deleted successfully",
            data=None,
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["get"])
    def complete_list(self, request):
        """Get complete list including soft-deleted records."""
        queryset = self.get_queryset().model.all_objects.all()
        serializer = self.get_serializer(queryset, many=True)
        return ApiResponse.success(
            message=f"{self.entity_name} full list retrieved successfully",
            data=serializer.data,
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["get"])
    def deleted_data_list(self, request):
        """Get list of soft-deleted records only."""
        queryset = self.get_queryset().model.all_objects.filter(is_deleted=True)
        serializer = self.get_serializer(queryset, many=True)
        return ApiResponse.success(
            message=f"{self.entity_name} deleted list retrieved successfully",
            data=serializer.data,
            status=status.HTTP_200_OK,
        )

    def list(self, request, *args, **kwargs):
        """Get paginated list of active records with standardized response."""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return ApiResponse.success(
            message=f"{self.entity_name} list retrieved successfully",
            data=serializer.data,
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"])
    def restore(self, request, pk=None):
        """Restore a soft-deleted record to active status."""
        instance = self.get_queryset().model.all_objects.get(pk=pk)
        instance.restore()

        return ApiResponse.success(
            message=f"{self.entity_name} restored successfully",
            data=None,
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["delete"])
    def force_delete(self, request, pk=None):
        """Permanently delete record from database (cannot be undone)."""
        instance = self.get_queryset().model.all_objects.get(pk=pk)
        instance.force_delete()

        return ApiResponse.success(
            message=f"{self.entity_name} permanently deleted",
            data=None,
            status=status.HTTP_200_OK,
        )
