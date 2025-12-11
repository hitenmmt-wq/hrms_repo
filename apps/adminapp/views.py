from django.shortcuts import render, get_object_or_404
from rest_framework import viewsets, filters
from apps.adminapp import models
from apps.adminapp import serializers
from rest_framework.response import Response
from rest_framework.decorators import APIView
import datetime
from django.utils import timezone
from apps.base.response import ApiResponse
from apps.base.permissions import IsAdmin,IsEmployee
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from django.core.mail import send_mail  
from django.conf import settings
from apps.adminapp.filters import HolidayFilter
from django_filters.rest_framework import DjangoFilterBackend
from apps.base.viewset import BaseViewSet

# Create your views here.

#  =============================================  USER AUTHENTICATION ==================================================================

class AdminRegister(BaseViewSet):
    queryset = models.Users.objects.all()
    serializer_class = serializers.AdminRegisterSerializer

    def create(self, request):
        data = request.data
        print(data)
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token = RefreshToken.for_user(user).access_token
            
            activation_link = base.constants.ACCOUNT_ACTIVATION_URL  # f"http://127.0.0.1:8000/adminapp/activate/{token}/"

            send_mail(
                subject="Activate your account",
                message=f"Click here to activate your account: /n {activation_link}",
                from_email = settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )

            return Response({"message": "User created successfully"}, status=201)
        return Response(serializer.errors, status=400)


class ActivateUser(APIView):
    def get(self, request, token):
        try:
            access_token = AccessToken(token)
            user_id = access_token['user_id']

            user = get_object_or_404(models.Users, id=user_id)

            if not user.is_active:
                user.is_active = True
                user.save()
                return Response({"message": "Account activated successfully! You can now login."})
            else:
                return Response({"message": "Account already activated."})

        except Exception as e:
            return Response({"error": "Invalid or expired token"}, status=400)
        
#  =============================================  HOLIDAY CRUD API ==================================================================
    
class HolidayViewSet(BaseViewSet):
    entity_name = "Holiday"
    permission_classes = [IsAdmin]
    queryset = models.Holiday.objects.all()
    serializer_class = serializers.HolidaySerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = HolidayFilter
    search_fields = ["name"]
    ordering_fields = ["date", "name"]
    ordering = ["date"]   
    
    def get_queryset(self):
        queryset = super().get_queryset()
        year = self.request.query_params.get("year", timezone.now().year)
        return queryset.filter(date__year=year)
    
    # def create(self, request, *args, **kwargs):
    #     serializer = self.get_serializer(data=request.data)
    #     serializer.is_valid(raise_exception=True)
    #     self.perform_create(serializer)
    #     return ApiResponse.success(self.entity_name, serializer.data)
    
    # def update(self, request, *args, **kwargs):
    #     instance = self.get_object()
    #     serializer = self.get_serializer(instance, data=request.data, partial=True)
    #     serializer.is_valid(raise_exception=True)
    #     self.perform_update(serializer)
    #     return ApiResponse.success(self.entity_name, serializer.data)

    # def destroy(self, request, *args, **kwargs):
    #     instance = self.get_object()
    #     self.perform_destroy(instance)
    #     return ApiResponse.success(self.entity_name)
    
#  =============================================  DEPARTMENT CRUD API ==================================================================

class DepartmentViewSet(BaseViewSet):
    entity_name = "Department"
    permission_classes = [IsAdmin]
    queryset = models.Department.objects.all()
    serializer_class = serializers.DepartmentSerializer
    search_fields = ["name"]
    ordering_fields = ["name"]
    ordering = ["name"]
    