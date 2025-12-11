from rest_framework import viewsets, status
from apps.base.response import ApiResponse

class BaseViewSet(viewsets.ModelViewSet):

    entity_name: str = None  

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        return ApiResponse.success(
            message=f"{self.entity_name} created successfully",
            data=serializer.data,
            status=status.HTTP_201_CREATED
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return ApiResponse.success(
            message=f"{self.entity_name} updated successfully",
            data=serializer.data,
            status=status.HTTP_200_OK
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)

        return ApiResponse.success(
            message=f"{self.entity_name} deleted successfully",
            data=None,
            status=status.HTTP_200_OK
        )
