from rest_framework.response import Response

class ApiResponse:
    @staticmethod
    def success(message: str, data=None, status=200):
        return Response({
            "success": True,
            "message": message,
            "data": data
        }, status=status)

    @staticmethod
    def error(message: str, errors=None, status=400):
        return Response({
            "success": False,
            "message": message,
            "errors": errors
        }, status=status)