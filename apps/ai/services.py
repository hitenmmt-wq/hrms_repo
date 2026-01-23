import uuid
from typing import Any, Dict

from channels.db import database_sync_to_async
from django.utils import timezone

from apps.ai.hugging_face import HuggingFaceLLM
from apps.ai.models import AIConversation, AIMessage, AIQueryLog
from apps.ai.utils import IntentClassifier
from apps.attendance.models import EmployeeAttendance
from apps.employee.models import LeaveBalance, PaySlip
from apps.superadmin.models import (
    Announcement,
    CommonData,
    Department,
    Holiday,
    Leave,
    LeaveType,
    Position,
    Users,
)


class AIService:
    """Core AI service for handling chatbot interactions."""

    def __init__(self, user):
        self.user = user
        self.role = user.role

    async def process_query(
        self, message: str, conversation_id: str = None
    ) -> Dict[str, Any]:
        """Process user query and generate AI response."""

        # Get or create conversation
        conversation = await self._get_or_create_conversation(conversation_id)

        # Save user message
        await self._save_message(conversation, "user", message)

        # Classify intent and build context
        intent = self._classify_intent(message)
        print(f"==>> intent: {intent}")
        context_data = await self._build_context(message, intent)

        # Generate AI response (placeholder for actual AI integration)
        ai_response = self._generate_response(message, context_data, intent)

        # Save AI response
        ai_message = await self._save_message(
            conversation,
            "ai",
            ai_response,
            metadata={"intent": intent, "context_used": list(context_data.keys())},
        )

        await self._ai_query_log(
            self.user, ai_response, ai_message, intent, list(context_data.keys())
        )

        return {
            "response": ai_response,
            "conversation_id": conversation.session_id,
            "message_id": ai_message.id,
        }

    @database_sync_to_async
    def _get_or_create_conversation(
        self, conversation_id: str = None
    ) -> AIConversation:
        """Get existing or create new conversation."""
        if conversation_id:
            try:
                return AIConversation.objects.get(
                    session_id=conversation_id, user=self.user
                )
            except AIConversation.DoesNotExist:
                pass

        return AIConversation.objects.create(
            user=self.user, session_id=str(uuid.uuid4())
        )

    @database_sync_to_async
    def _save_message(self, conversation, msg_type, content, metadata=None):
        return AIMessage.objects.create(
            conversation=conversation,
            message_type=msg_type,
            content=content[0] if msg_type == "ai" else content,
            response_time=content[1] if content and msg_type == "ai" else None,
            metadata=metadata or {},
        )

    @database_sync_to_async
    def _ai_query_log(self, user, message, ai_message, intent, context_used):
        return AIQueryLog.objects.create(
            user=user,
            ai_message=ai_message,
            query=message[0] if message else None,
            intent=intent,
            data_accessed=context_used,
            processing_time=message[1] if message else None,
        )

    def _classify_intent(self, message: str) -> str:
        """Classify user intent from message."""
        message_lower = message.lower()
        print(f"==>> message_lower: {message_lower}")

        intent_confidence = IntentClassifier.classify(message_lower)
        print(f"==>> intent_confidence: {intent_confidence}")
        return intent_confidence

    async def _build_context(self, message: str, intent: str) -> Dict[str, Any]:
        """Build context data based on user role and intent."""
        context = {}

        if intent == "leave_inquiry":
            context.update(await self._get_leave_context())
        elif intent == "attendance_inquiry":
            context.update(await self._get_attendance_context())
        elif intent == "payroll_inquiry":
            context.update(await self._get_payroll_context())
        elif intent == "profile_inquiry":
            context.update(await self._get_profile_context())
        elif intent == "general_inquiry":
            context.update(await self._get_general_context())

        return context

    @database_sync_to_async
    def _get_leave_context(self) -> Dict[str, Any]:
        """Get leave-related context based on user role."""
        context = {}

        if self.role in ["admin", "hr"]:
            # Admin/HR can see all leave data
            context["pending_leaves"] = Leave.objects.filter(status="pending").count()
            context["total_employees"] = Users.objects.filter(role="employee").count()

        if self.role == "employee" or self.role in ["admin", "hr"]:
            # Employee sees own data, admin/hr can see in context of specific queries
            try:
                leave_balance = LeaveBalance.objects.get(employee=self.user)
                context["my_leave_balance"] = {
                    "employee": leave_balance.employee,
                    "year": leave_balance.year,
                    "pl_leave": leave_balance.pl,
                    "sl_leave": leave_balance.sl,
                    "lop_leave": leave_balance.lop,
                    "used_pl": leave_balance.used_pl,
                    "used_sl": leave_balance.used_sl,
                    "used_lop": leave_balance.used_lop,
                }
            except LeaveBalance.DoesNotExist:
                context["my_leave_balance"] = None

        return context

    @database_sync_to_async
    def _get_attendance_context(self) -> Dict[str, Any]:
        """Get attendance-related context."""
        context = {}

        if self.role == "employee":
            # Employee's own attendance
            recent_attendance = EmployeeAttendance.objects.filter(
                employee=self.user
            ).order_by("-date")[:5]
            context["my_recent_attendance"] = [
                {
                    "employee": att.employee,
                    "day": att.day,
                    "status": att.status,
                    "check_in": att.check_in,
                    "check_out": att.check_out,
                    "work_hours": att.work_hours,
                    "break_hours": att.break_hours,
                }
                for att in recent_attendance
            ]
        else:
            employees = EmployeeAttendance.objects.filter(
                day=timezone.now().date()
            ).values(
                "check_in",
                "check_out",
                "status",
                "work_hours",
                "break_hours",
                "day",
                "employee__first_name",
                "employee__last_name",
            )
            context["my_recent_attendance"] = list(employees)

        return context

    @database_sync_to_async
    def _get_payroll_context(self) -> Dict[str, Any]:
        """Get payroll-related context."""
        context = {}

        if self.role == "employee":
            # Employee's own payslips
            recent_payslips = PaySlip.objects.filter(employee=self.user).order_by(
                "-created_at"
            )[:5]
            context["my_recent_payslips"] = [
                {
                    "employee": ps.employee,
                    "start_date": ps.start_date,
                    "end_date": ps.end_date,
                    "month": ps.month,
                    "days": ps.days,
                    "basic_salary": ps.basic_salary,
                    "hr_allowance": ps.hr_allowance,
                    "special_allowance": ps.special_allowance,
                    "total_earnings": ps.total_earnings,
                    "other_deductions": ps.other_deductions,
                    "leave_deductions": ps.leave_deductions,
                    "tax_deductions": ps.tax_deductions,
                    "total_deductions": ps.total_deductions,
                    "net_salary": ps.net_salary,
                    "pdf_file": ps.pdf_file.url if ps.pdf_file else None,
                }
                for ps in recent_payslips
            ]
        elif self.role in ["admin", "hr"]:
            # Admin/HR summary data
            context["total_payslips_generated"] = PaySlip.objects.count()
            recent_payslips = PaySlip.objects.all().order_by("-created_at")[:10]
            context["my_recent_payslips"] = [
                {
                    "employee": ps.employee,
                    "start_date": ps.start_date,
                    "end_date": ps.end_date,
                    "month": ps.month,
                    "days": ps.days,
                    "basic_salary": ps.basic_salary,
                    "hr_allowance": ps.hr_allowance,
                    "special_allowance": ps.special_allowance,
                    "total_earnings": ps.total_earnings,
                    "other_deductions": ps.other_deductions,
                    "leave_deductions": ps.leave_deductions,
                    "tax_deductions": ps.tax_deductions,
                    "total_deductions": ps.total_deductions,
                    "net_salary": ps.net_salary,
                    "pdf_file": ps.pdf_file.url if ps.pdf_file else None,
                }
                for ps in recent_payslips
            ]

        return context

    @database_sync_to_async
    def _get_profile_context(self) -> Dict[str, Any]:
        """Get profile-related context."""
        context = {}

        context["my_profile"] = {
            "name": f"{self.user.first_name} {self.user.last_name}",
            "email": self.user.email,
            "role": self.user.role,
            "position": self.user.position.name if self.user.position else None,
            "department": self.user.department.name if self.user.department else None,
            "joining_date": self.user.joining_date,
            "birthdate": self.user.birthdate,
            "salary_ctc": self.user.salary_ctc,
            "profile_image": self.user.profile.url if self.user.profile else None,
        }

        return context

    @database_sync_to_async
    def _get_general_context(self) -> Dict[str, Any]:
        """Get general company context."""
        context = {}

        if self.role in ["admin", "hr"]:
            context["company_stats"] = {
                "total_employees": (Users.objects.filter(role="employee").count)(),
                "total_departments": (Department.objects.count)(),
                "total_positions": (Position.objects.count)(),
                "announcements": list(
                    Announcement.objects.values("title", "created_at")
                ),
                "common_data": (CommonData.objects.first)(),
                "leave_types": list(LeaveType.objects.values("name", "code")),
                "holidays": (list(Holiday.objects.values("name", "date"))),
            }

        return context

    def _build_prompt(self, message: str, context: Dict[str, Any]) -> str:
        prompt = f"""
        You are an  HRMS AI assistant.
        User Role : {self.role}
        User question : {message}
        Relevant HRMS data (from DB) : {context}

        Rules :
        - Use only the provided data
        - do not guess
        - be concise and professional
        - little bit of exaggration will be good
        - Below are rules for different type of user as per their roles.
        - Be carefull when particular intent is fetched as there are many tables from which data are being fetched.
          So decide properly which data to use in response. That will help in better response generation.
          Also from that table many columns select data set as needed to user question.

        - 'employee': You are a helpful HRMS Assistant for employees.
            You assist with:
            - Leave balance and application status
            - Attendance records and statistics
            - Payslip information
            - Personal profile information
            - General HR policies and procedures

            Rules:
            1. Only show the user their own data
            2. Be concise and friendly
            3. If data is not available, suggest checking the HRMS system directly
            4. Never provide other employees' data
            5. Use simple, non-technical language,

        - 'hr': You are an HR Assistant for HR personnel.
            You help with:
            - Leave management (pending, approved, rejected applications)
            - Employee information and search
            - Attendance tracking and analytics
            - Payroll summaries
            - Company policies and procedures
            - Department and position information

            Rules:
            1. You can access all employee data
            2. Provide insights and summaries
            3. Help with decision-making
            4. Be professional and detail-oriented
            5. Highlight important trends or issues,

        - 'admin': You are the HRMS System Administrator Assistant.
            You have full access to:
            - All employee and company data
            - System analytics and reports
            - Configuration information
            - Access logs and activity
            - Performance metrics

            Rules:
            1. You have full system access
            2. Provide comprehensive data and insights
            3. Help with system management and optimization
            4. Highlight critical issues
            5. Provide technical details when relevant,
        """
        return prompt

    def _generate_response(
        self, message: str, context: Dict[str, Any], intent: str
    ) -> str:
        print(f"==>> context: {context}")
        """Generate AI response based on context and intent."""
        # Placeholder for actual AI integration
        # This would integrate with OpenAI, Claude, or other LLM APIs

        if intent == "greeting":
            return f"Hello {self.user.first_name}! I'm your HRMS AI assistant. How can I help you today?"

        prompt = self._build_prompt(message, context)
        try:
            llm = HuggingFaceLLM()
            response = llm.generate(prompt)
            return response
        except Exception as e:
            print("HF ERROR:", str(e))
            return "I'm having trouble generating a response right now. Please try again in a moment."


class ContextBuilder:
    """Helper class for building AI context from database."""

    @staticmethod
    def get_user_accessible_data(user, data_type: str) -> Dict[str, Any]:
        """Get data accessible to user based on their role."""

        if data_type == "employees" and user.role in ["admin", "hr"]:
            return {
                "total_employees": Users.objects.filter(role="employee").count(),
                "departments": list(Department.objects.values("name")),
            }

        elif data_type == "company_info":
            return {
                "holidays": list(
                    Holiday.objects.filter(date__year=2024).values("name", "date")
                ),
                "departments": list(Department.objects.values("name")),
            }

        return {}
