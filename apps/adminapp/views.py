from django.shortcuts import render, get_object_or_404
from rest_framework import viewsets, filters
from apps.adminapp import models
from apps.adminapp import serializers
from rest_framework.response import Response
from rest_framework.decorators import APIView
import datetime
from django.utils import timezone
from apps.base.response import ApiResponse
from apps.base.permissions import IsAdmin, IsEmployee, IsAuthenticated, IsHr
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from django.core.mail import send_mail  
from django.conf import settings
from apps.adminapp.filters import HolidayFilter
from django_filters.rest_framework import DjangoFilterBackend
from apps.base.viewset import BaseViewSet
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework_simplejwt.views import TokenObtainPairView
import jwt
from apps.adminapp.tasks import send_email_task
# Create your views here.

#  =============================================  USER AUTHENTICATION ==================================================================

class ChangePassword(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        old_pass = request.data.get("old_password")
        new_pass = request.data.get("new_password")
        confirm_new_pass = request.data.get("confirm_new_pass")

        if not user.check_password(old_pass):
            return ApiResponse.error({"error": "Old password is incorrect."}, status=400)
        
        if new_pass != confirm_new_pass:
            return ApiResponse.error({"error": "New passwords do not match."}, status=400)

        user.set_password(new_pass)
        user.save()

        return ApiResponse.success({"message": "Password updated successfully."}, status=200)


class ResetPassword(APIView):
    def post(self, request):
        email = request.data.get("email")
        print(f"==>> email: {email}")
        try:
            user = models.Users.objects.get(email=email)
            print(f"==>> user: {user}")
        except models.Users.DoesNotExist:
            return Response({"error": "User with this email does not exist"}, status=404)

        token = jwt.encode({"user_id": user.id}, settings.SECRET_KEY, algorithm="HS256")
        reset_link = f"http://127.0.0.1:8000/adminapp/auth/confirm_reset_password/{token}"

        send_email_task.delay(
            subject="Reset Password",
            to_email=user.email,
            text_body=f"Use this link to reset your password: {reset_link}",
        )

        return Response({"message": "Password reset link sent successfully"})
    
class VerifyResetLink(APIView):
    def post(self, request):
        uid = request.data.get("uid")
        token = request.data.get("token")
        new_password = request.data.get("new_password")

        try:
            user_id = force_str(urlsafe_base64_decode(uid))
            user = User.objects.filter(pk=user_id).first()
        except:
            return Response({"message": "Invalid link"}, status=400)

        if PasswordResetTokenGenerator().check_token(user, token):
            return Response({"valid": True})
        else:
            return Response({"valid": False}, status=400)
    
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
            
            activation_link = apps.base.constants.ACCOUNT_ACTIVATION_URL  # f"http://127.0.0.1:8000/adminapp/activate/{token}/"

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
        
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = serializers.CustomTokenObtainPairSerializer
    
class UserViewSet(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = serializers.UserSerializer(request.user)
        return Response(serializer.data)
    
#  =============================================  HOLIDAY CRUD API ==================================================================
    
class HolidayViewSet(BaseViewSet):
    entity_name = "Holiday"
    permission_classes = [IsAdmin]
    queryset = models.Holiday.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = HolidayFilter
    search_fields = ["name"]
    ordering_fields = ["date", "name"]
    ordering = ["date"]   
    
    def get_serializer_class(self):
        if self.action == "list":
            return serializers.HolidayListSerializer
        return serializers.HolidaySerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        year = self.request.query_params.get("year", timezone.now().year)
        return queryset.filter(date__year=year)
    
    
#  =============================================  DEPARTMENT CRUD API ==================================================================

class DepartmentViewSet(BaseViewSet):
    entity_name = "Department"
    permission_classes = [IsAdmin]
    queryset = models.Department.objects.all()
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["name"]
    search_fields = ["name"]
    ordering_fields = ["name"]
    ordering = ["name"]
    
    def get_serializer_class(self):
        if self.action == "list":
            return serializers.DepartmentListSerializer
        return serializers.DepartmentSerializer
    
#  =============================================  PROFILE CRUD API ==================================================================

class ProfileViewSet(BaseViewSet):
    entity_name = "Profile"
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.ProfileSerializer
    queryset = models.Users.objects.all()
    search_fields = ["email"]
    ordering_fields = ["email"]
    ordering = ["email"]
    
    def get_serializer_class(self):
        if self.action == "update":
            return serializers.ProfileUpdateSerializer
        return serializers.ProfileSerializer
    
