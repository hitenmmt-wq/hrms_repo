from datetime import datetime, time

from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import APIView, action
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.attendance.models import EmployeeAttendance
from apps.base import constants
from apps.base.pagination import CustomPageNumberPagination
from apps.base.permissions import IsAdmin, IsAuthenticated
from apps.base.response import ApiResponse
from apps.base.viewset import BaseViewSet
from apps.employee.utils import employee_monthly_working_hours
from apps.superadmin import models, serializers
from apps.superadmin.custom_filters import (
    AnnouncementFilter,
    DepartmentFilter,
    HolidayFilter,
    LeaveFilter,
    LeaveTypeFilter,
    PositionFilter,
    SuperAdminFilter,
)
from apps.superadmin.tasks import send_email_task
from apps.superadmin.utils import (
    notify_employee_leave_approved,
    notify_employee_leave_rejected,
    update_leave_balance,
)

# Create your views here.

#   ================  CUSTOM SCRIPT    ========


class CustomScriptView(APIView):
    def get(self, request):

        # employee_attendance = EmployeeAttendance.objects.create
        print("hiiiiiii iiiiiiiiiiiiiiiiiiiiii")
        return ApiResponse.success({"message": "script worked successfully"})


#   ================  ADMIN DASHBOARD    ========


class AdminDashboardView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        try:
            today = timezone.now().date()
            late_time = timezone.make_aware(datetime.combine(today, time(10, 5)))
            total_employees = models.Users.objects.filter(is_active=True)
            pending_approval_count = models.Leave.objects.filter(
                status="pending", from_date__gte=today
            )
            present_employee = EmployeeAttendance.objects.filter(day=today)
            absent_employee = total_employees.exclude(
                id__in=present_employee.values_list("employee_id", flat=True)
            )

            current_birthdays = models.Users.objects.filter(
                is_active=True, birthdate__month=today.month, birthdate__day=today.day
            )
            upcoming_leaves = models.Leave.objects.filter(
                status="approved", from_date__gte=today
            )[:10]
            upcoming_holidays = models.Holiday.objects.filter(
                date__year=timezone.now().year, date__gte=today
            ).order_by("date")
            late_logins = EmployeeAttendance.objects.filter(
                day=today, check_in__gt=late_time
            )
            recent_joiners = models.Users.objects.filter(is_active=True).order_by(
                "-id"
            )[:3]

            announcement = models.Announcement.objects.all().order_by("-id")[:5]

            total_employees_active = total_employees.filter(
                role=constants.EMPLOYEE_USER
            )
            team_monthly_working_hour = {}
            for employee in total_employees_active:
                team_monthly_working_hour[employee.id] = employee_monthly_working_hours(
                    employee
                )

            data = {
                "counts": {
                    "total_employees": total_employees.count(),
                    "present_employee": present_employee.count(),
                    "absent_employee": absent_employee.count(),
                    "pending_approvals": pending_approval_count.count(),
                },
                "team_monthly_working_hour": team_monthly_working_hour,
                "current_birthdays": serializers.UserMiniSerializer(
                    current_birthdays, many=True
                ).data,
                "upcoming_leaves": serializers.LeaveMiniSerializer(
                    upcoming_leaves, many=True
                ).data,
                "upcoming_holidays": serializers.HolidayMiniSerializer(
                    upcoming_holidays, many=True
                ).data,
                "recent_joiners": serializers.UserMiniSerializer(
                    recent_joiners, many=True
                ).data,
                "present_employee": serializers.EmployeeAttendanceMiniSerializer(
                    present_employee, many=True
                ).data,
                "absent_employee": serializers.UserMiniSerializer(
                    absent_employee, many=True
                ).data,
                "late_logins": serializers.LateLoginMiniSerializer(
                    late_logins, many=True
                ).data,
                "announcement": serializers.AnnouncementListSerializer(
                    announcement, many=True
                ).data,
            }

            return ApiResponse.success(
                message="dashboard fetched successfully", data=data
            )

        except Exception as e:
            return ApiResponse.error(
                message="Failed to load dashboard",
                errors=str(e),
                status=500,
            )


#   ================  USER AUTHENTICATION   ========


class ChangePassword(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        old_pass = request.data.get("old_password")
        new_pass = request.data.get("new_password")
        confirm_new_pass = request.data.get("confirm_new_pass")

        if not user.check_password(old_pass):
            return ApiResponse.error(
                {"error": "Old password is incorrect."}, status=400
            )

        if new_pass != confirm_new_pass:
            return ApiResponse.error(
                {"error": "New passwords do not match."}, status=400
            )

        user.set_password(new_pass)
        user.save()

        return ApiResponse.success(
            {"message": "Password updated successfully."}, status=200
        )


class ResetPassword(APIView):
    def post(self, request):
        email = request.data.get("email")
        try:
            user = models.Users.objects.filter(email=email).first()
        except models.Users.DoesNotExist:
            return Response(
                {"error": "User with this email does not exist"}, status=404
            )

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = PasswordResetTokenGenerator().make_token(user)
        localhost = "http://127.0.0.1:8000/"

        reset_link = (
            f"{localhost}adminapp/auth/confirm_reset_password/?uid={uid}&?token={token}"
        )

        send_email_task.delay(
            subject="Reset Password",
            to_email=user.email,
            text_body=f"Use this link to reset your password: {reset_link}",
        )

        return Response({"message": "Password reset link sent successfully"})


class ResetPasswordChange(APIView):
    def post(self, request):
        uid = request.data.get("uid")
        token = request.data.get("token")
        new_password = request.data.get("new_password")
        confirm_password = request.data.get("confirm_password")

        if new_password != confirm_password:
            return Response({"error": "Passwords do not match"}, status=400)

        try:
            user_id = force_str(urlsafe_base64_decode(uid))
            user = models.Users.objects.filter(pk=user_id).first()
        except Exception as e:
            return Response({"error": f"Invalid reset link, {e}"}, status=400)

        if not PasswordResetTokenGenerator().check_token(user, token):
            return Response({"error": "Invalid or expired token"}, status=400)

        user.set_password(new_password)
        user.save(update_fields=["password"])

        return Response({"message": "Password reset successful"})


class AdminRegister(BaseViewSet):
    entity_name = "Super-Admin"
    queryset = models.Users.objects.filter(role=constants.ADMIN_USER)
    serializer_class = serializers.AdminRegisterSerializer
    pagination_class = CustomPageNumberPagination
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = SuperAdminFilter
    search_fields = ["email", "first_name", "last_name", "role"]
    ordering_fields = ["email", "first_name"]
    ordering = ["email"]

    def create(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            user = serializer.save()

            activation_link = (
                constants.ACCOUNT_ACTIVATION_URL
            )  # f"http://127.0.0.1:8000/adminapp/activate/{token}/"
            try:
                print("startssssssssssssssssss")
                send_email_task.delay(
                    subject="Activate your account",
                    to_email=user.email,
                    text_body=f"Click here to activate your account: {activation_link}",
                )
            except Exception as e:
                print("Error here.........", e)

            return Response({"message": "User created successfully"}, status=201)
        return Response(serializer.errors, status=400)

    def get_serializer_class(self):
        if self.action == "create":
            return serializers.AdminRegisterSerializer
        elif self.action == "update":
            return serializers.AdminUpdateSerializer
        else:
            return serializers.AdminListSerializer


class ActivateUser(APIView):
    def get(self, request, token):
        try:
            access_token = AccessToken(token)
            user_id = access_token["user_id"]

            user = get_object_or_404(models.Users, id=user_id)

            if not user.is_active:
                user.is_active = True
                user.save()
                try:
                    print("started ....!!")
                    send_email_task.delay(
                        subject="Welcome to HRMS",
                        body=f"You have been added to HRMS portal as {user.role}. Please Login to continue.",
                        to=user.email,
                    )
                    print("done successfully...")
                except Exception as e:
                    print("Error here.........", e)
                return Response(
                    {"message": "Account activated successfully! You can now login."}
                )
            else:
                return Response({"message": "Account already activated."})

        except Exception:
            return Response({"error": "Invalid or expired token"}, status=400)


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = serializers.CustomTokenObtainPairSerializer


class UserViewSet(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = serializers.UserSerializer(request.user)
        return Response(serializer.data)


#   ================  COMMON_DATA CRUD API   ========


class CommonDataViewSet(BaseViewSet):
    entity_name = "Common Data"
    permission_classes = [IsAdmin]
    queryset = models.CommonData.objects.all()
    serializer_class = serializers.CommonDataSerializer
    pagination_class = None

    def list(self, request, *args, **kwargs):
        instance = self.get_queryset().first()
        if not instance:
            return ApiResponse.success(message="Common Data not available", data=None)

        serializer = self.get_serializer(instance)
        return ApiResponse.success(
            message="Common Data Fetched successfully", data=serializer.data
        )

    def create(self, request, *args, **kwargs):
        instance = self.get_queryset().first()
        if instance:
            return ApiResponse.error(
                message="Common Data already exists. You can update it.", status=400
            )
        else:
            serializer = self.serializer_class(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return ApiResponse.success(
                message="Common Data created successfully",
                data=serializer.data,
                status=201,
            )

    @action(detail=False, methods=["patch"], url_path="update")
    def update_common_data(self, request, *args, **kwargs):
        instance = self.get_queryset().first()
        if not instance:
            return ApiResponse.error(
                message="Common Data not available to update", status=404
            )
        else:
            serializer = self.get_serializer(instance, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return ApiResponse.success(
                message="Common Data updated successfully", data=serializer.data
            )

    @action(detail=False, methods=["delete"], url_path="delete")
    def destroy_common_data(self, request, *args, **kwargs):
        instance = self.get_queryset().first()
        if not instance:
            return ApiResponse.error(
                message="Common Data not available to delete", status=404
            )
        else:
            instance.delete()
            return ApiResponse.success(message="Common Data deleted successfully")


#   ================  SETTING_DATA CRUD API   ========


class SettingDataViewSet(BaseViewSet):
    entity_name = "Setting Data"
    permission_classes = [IsAdmin]
    serializer_class = serializers.SettingDataSerializer
    queryset = models.SettingData.objects.all()
    pagination_class = None

    def list(self, request, *args, **kwargs):
        instance = self.get_queryset().first()
        if not instance:
            return ApiResponse.success(message="Setting Data not available", data=None)

        serializer = self.get_serializer(instance)
        return ApiResponse.success(
            message="Setting Data Fetched successfully", data=serializer.data
        )

    def create(self, request, *args, **kwargs):
        instance = self.get_queryset().first()
        if instance:
            return ApiResponse.error(
                message="Setting Data already exists. You can update it.", status=400
            )
        else:
            serializer = self.serializer_class(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return ApiResponse.success(
                message="Setting Data created successfully",
                data=serializer.data,
                status=201,
            )

    @action(detail=False, methods=["patch"], url_path="update")
    def update_setting_data(self, request, *args, **kwargs):
        instance = self.get_queryset().first()
        if not instance:
            return ApiResponse.error(
                message="Setting Data not available to update", status=404
            )
        else:
            serializer = self.get_serializer(instance, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return ApiResponse.success(
                message="Setting Data updated successfully",
                data=serializer.data,
                status=200,
            )

    @action(detail=False, methods=["delete"], url_path="delete")
    def delete_setting_data(self, request, *args, **kwargs):
        instance = self.get_queryset().first()
        if not instance:
            return ApiResponse.error(
                message="Setting Data not available to delete", status=404
            )
        else:
            instance.delete()
            return ApiResponse.success(
                message="Setting Data deleted successfully", status=200
            )


#   ================  HOLIDAY CRUD API   ========


class HolidayViewSet(BaseViewSet):
    entity_name = "Holiday"
    permission_classes = [IsAdmin]
    queryset = models.Holiday.objects.all()
    pagination_class = CustomPageNumberPagination
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
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


#   ================  LEAVE_TYPE CRUD API   ========


class LeaveTypeViewSet(BaseViewSet):
    entity_name = "LeaveType"
    permission_classes = [IsAdmin]
    serializer_class = serializers.LeaveTypeSerializer
    queryset = models.LeaveType.objects.all()
    pagination_class = CustomPageNumberPagination
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = LeaveTypeFilter
    search_fields = ["name", "code"]
    ordering_fields = ["name", "code"]
    ordering = ["name"]

    def get_serializer_class(self):
        if self.action == "list":
            return serializers.LeaveTypeListSerializer
        return serializers.LeaveTypeSerializer


#   ================  DEPARTMENT CRUD API   ========


class DepartmentViewSet(BaseViewSet):
    entity_name = "Department"
    permission_classes = [IsAdmin]
    queryset = models.Department.objects.all()
    pagination_class = CustomPageNumberPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    filterset_class = DepartmentFilter
    filterset_fields = ["name"]
    search_fields = ["name"]
    ordering_fields = ["name"]
    ordering = ["name"]

    def get_serializer_class(self):
        if self.action == "list":
            return serializers.DepartmentListSerializer
        return serializers.DepartmentSerializer


#   ================  ANNOUNCEMENT CRUD API   ========


class AnnouncementViewSet(BaseViewSet):
    entity_name = "Announcement"
    permission_classes = [IsAdmin]
    queryset = models.Announcement.objects.all()
    pagination_class = CustomPageNumberPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    filterset_class = AnnouncementFilter
    search_fields = ["title", "date"]
    ordering_fields = ["date"]
    ordering = ["date"]

    def get_serializer_class(self):
        if self.action == "list":
            return serializers.AnnouncementListSerializer
        return serializers.AnnouncementSerializer


#   ================  POSITION CRUD API   ========


class PositionViewSet(BaseViewSet):
    entity_name = "Position"
    permission_classes = [IsAdmin]
    queryset = models.Position.objects.all()
    pagination_class = CustomPageNumberPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    filterset_class = PositionFilter
    filterset_fields = ["name"]
    search_fields = ["name"]
    ordering_fields = ["name"]
    ordering = ["name"]

    def get_serializer_class(self):
        if self.action == "list":
            return serializers.PositionListSerializer
        return serializers.PositionSerializer


#   ================  PROFILE CRUD API   ========


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


#  ==============  LEAVES CRUD API ====================


class LeaveViewSet(viewsets.ModelViewSet):

    queryset = (
        models.Leave.objects.select_related("employee", "approved_by")
        .all()
        .order_by("-from_date")
    )
    serializer_class = serializers.LeaveSerializer
    permission_classes = [IsAuthenticated]
    filterset_class = LeaveFilter
    pagination_class = CustomPageNumberPagination

    def get_queryset(self):
        user = self.request.user
        if user.role == constants.ADMIN_USER:
            return super().get_queryset()
        return super().get_queryset().filter(employee=user)

    def get_serializer_class(self):
        if self.action == "create":
            return serializers.LeaveApplySerializer
        return serializers.LeaveSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        leave = serializer.save()
        return ApiResponse.success(
            message="Leave applied successfully",
            data=serializers.LeaveSerializer(leave).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def cancel(self, request, pk=None):
        leave = get_object_or_404(models.Leave, id=pk, employee=request.user)
        if leave.status == "approved":
            return ApiResponse.error("Cannot cancel approved leave", status=400)
        leave.status = "cancelled"
        leave.save(update_fields=["status"])
        return ApiResponse.success("Leave cancelled")


class LeaveApprovalViewSet(BaseViewSet):
    permission_classes = [IsAdmin]

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        user = request.user
        try:
            leave_data = models.Leave.objects.filter(id=pk).first()
            leave_data.status = constants.APPROVED
            leave_data.approved_at = datetime.now()
            leave_data.approved_by = user
            leave_data.response_text = request.data.get("response_text", "")
            leave_data.save(
                update_fields=["status", "approved_by", "approved_at", "response_text"]
            )
            update_leave_balance(
                leave_data.employee,
                leave_data.leave_type,
                leave_data.status,
                leave_data.total_days,
            )
            EmployeeAttendance.objects.create(
                employee=leave_data.employee,
                day=leave_data.from_date,
                status=constants.PAID_LEAVE,
            )
            notify_employee_leave_approved(leave_data.employee, leave_data)

            serialize = serializers.LeaveSerializer(leave_data)
            return ApiResponse.success(
                message="Leave approved", data=serialize.data, status=status.HTTP_200_OK
            )
        except Exception as exc:
            return ApiResponse.error(str(exc), status=400)

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        user = request.user
        try:
            leave = models.Leave.objects.filter(id=pk).first()
            leave.status = constants.REJECTED
            leave.approved_by = user
            leave.approved_at = datetime.now()
            leave.response_text = request.data.get("response_text", "")
            leave.save(
                update_fields=["status", "approved_by", "approved_at", "response_text"]
            )

            update_leave_balance(
                leave.employee, leave.leave_type, leave.status, leave.total_days
            )
            notify_employee_leave_rejected(leave.employee, leave)

            serialize = serializers.LeaveSerializer(leave)
            return ApiResponse.success(
                message="Leave rejected", data=serialize.data, status=status.HTTP_200_OK
            )
        except Exception as exc:
            return ApiResponse.error(str(exc), status=400)
