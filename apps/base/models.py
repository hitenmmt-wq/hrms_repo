"""
Base models for HRMS with soft delete and timestamp functionality.

Provides BaseModel with automatic timestamps and soft delete capabilities
for all HRMS models to ensure consistent data management.
"""

from django.db import models
from django.utils import timezone


class SoftDeleteManager(models.Manager):
    """Manager for soft delete operations with filtered querysets."""

    def get_queryset(self):
        """Return only non-deleted records by default."""
        return super().get_queryset().filter(is_deleted=False)

    def with_deleted(self):
        """Return all records including soft-deleted ones."""
        return super().get_queryset()

    def deleted_only(self):
        """Return only soft-deleted records."""
        return super().get_queryset().filter(is_deleted=True)


class BaseModel(models.Model):
    """Abstract base model with timestamps and soft delete functionality."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    objects = SoftDeleteManager()
    all_objects = models.Manager()

    class Meta:
        abstract = True

    def delete(self):
        """Soft delete the record by marking as deleted."""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()

    def soft_delete(self):
        """Explicitly perform soft delete operation."""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()

    def restore(self):
        """Restore a soft-deleted record to active status."""
        self.is_deleted = False
        self.deleted_at = None
        self.save()

    def force_delete(self):
        """Permanently delete the record from database."""
        super().delete()
