import uuid
from typing import Any, Dict

from channels.db import database_sync_to_async
from django.utils import timezone

from apps.ai.hugging_face import HuggingFaceLLM
from apps.ai.models import AIConversation, AIMessage, AIQueryLog
from apps.ai.utils import (
    PromptTemplates,
    calculate_announcement_patterns,
    calculate_attendance_patterns,
    calculate_employee_patterns,
    calculate_general_patterns,
    calculate_holiday_patterns,
    calculate_leave_patterns,
    calculate_payroll_patterns,
    calculate_profile_patterns,
)
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
        conversation = await self._get_or_create_conversation(conversation_id, message)

        # Save user message
        await self._save_message(conversation, "user", message)

        # Classify intent and build context
        intent = self._classify_intent(message)
        print(f"==>> intent: {intent}")
        # intent = ('attendance_inquiry', 'payroll_inquiry', 1.297)
        context_data = await self._build_context(message, intent)
        print(f"==>> context_data: {context_data}")

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
        self, conversation_id: str = None, message: str = None
    ) -> AIConversation:
        """Get existing or create new conversation."""
        if conversation_id:
            try:
                return AIConversation.objects.get(
                    session_id=conversation_id, user=self.user
                )
            except AIConversation.DoesNotExist:
                pass

        title_prompt = self._generate_title_with_llm(message=message)
        try:
            llm = HuggingFaceLLM()
            title_response = llm.generate(title_prompt)
            title = title_response[0]
        except Exception as e:
            print("HF ERROR:", str(e))
            title = "Default Title"
        return AIConversation.objects.create(
            user=self.user, session_id=str(uuid.uuid4()), title=title
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
        print(
            f"==>> intent before saving -----------------------------------: {intent}"
        )
        return AIQueryLog.objects.create(
            user=user,
            ai_message=ai_message,
            query=message[0] if message else None,
            intent=intent,
            data_accessed=context_used,
            processing_time=message[1] if message else None,
        )

    @database_sync_to_async
    def get_ai_query_logs(self):
        return AIQueryLog.objects.all().order_by("-created_at")

    @database_sync_to_async
    def get_handbook_details(self):
        data = CommonData.objects.values_list("handbook_content")
        print(f"==>> data: {data}")
        return data

    def _classify_intent(self, message: str) -> str:
        """Classify user intent from message."""
        message_lower = message.lower()
        print(f"==>> message_lower: {message_lower}")

        ai_query_logs = self.get_ai_query_logs()
        prompt = f"""
            You are going to identify users requirements and classify which intent will be there as option are:
            - leave_inquiry
            - attendance_inquiry
            - payroll_inquiry
            - profile_inquiry
            - general_inquiry
            - holiday_inquiry
            - announcement_inquiry
            - department_inquiry
            - position_inquiry
            - common_data_inquiry
            - leave_type_inquiry
            - employee_inquiry
            - handbook_inquiry
            - greetings
            - other

            User message: {message_lower}

            Previous queries: {ai_query_logs}
            - From these logs you can fetch detailing of each response and
              users's feedback to response, if given by user.
            - If user is just greeting then, greet them back. dont provide data there.
            - Analyze user message then properly respond as required.
            - Upgrade and better each responses after learning from logs and user message.
            - Adapt responses but keep in mind that data would have been changed currently.
            - If you think user is asking same question again, then give response accordingly.
            - If you think user is asking something new, then give response accordingly.
            - If you think user is asking something which is not in above list, then give response with genearal intent.
            - Make sure here you are just returning intent of user as to fetch data as context data.
            - Intents can be multiple from the given list, dont just take first as default, check whole list properly.
            - There can be multiple intents like user might want to fetch attendance and payroll data simultaneously.
              so pass those multiple intents in tuple like ['attendance_inquiry', 'payroll_inquiry']
            - While returning intent list, only pass that only like , ['attendance_inquiry', 'payroll_inquiry'].
            - As im getting whole text suggesting how it came to conclusion, which  is not necessary.
            - when user want information regarding handbook, then give precise data and information, as this
              information should not be misunderstood. and give pproper response as mentioned in handbook details.
              nothing extra or out of the context or out of the box is required to be given.
            - Intent should always be one word or list of mutliple words only. should not add extra text anywhere.
            - Analyze intent properly on whole message provided because based on that
              further data will be fetched from DB.
            - Also if in same conversation ID, then get previous message/response's intent as well.
              Because next question or follow up question might be of same intent as well.
            - There might be chance where in same conversation responsd to follow up question as YES or NO.
              so based on that again update intent as it was in previous ones.
            - And if there's different conceptual intent added then we need to update intent
              with new and old accordingly.
            - At many points only new intent, only old intent or both combinely after adding/sunstracting
              will be forwarded to fetch context as per user's intentions.

            Classify the intent of the current query based on the user message and previous queries.
            Return only the intent name list as recognized from the above list.
        """

        try:
            llm = HuggingFaceLLM()
            response = llm.generate(prompt)
            print(f"==>> intent response generated....: {response}")
            return response[0] if response else None
        except Exception as e:
            print("HF ERROR:", str(e))
            return "I'm having trouble generating a response right now. Please try again in a moment."

    async def _build_context(self, message: str, intent: list) -> Dict[str, Any]:
        """Build context data based on user role and intent."""
        context = {}

        if "leave_inquiry" in intent:
            context.update(await self._get_leave_context())
        if "attendance_inquiry" in intent:
            context.update(await self._get_attendance_context())
        if "payroll_inquiry" in intent:
            context.update(await self._get_payroll_context())
        if "profile_inquiry" in intent:
            context.update(await self._get_profile_context())
        if "general_inquiry" in intent:
            context.update(await self._get_general_context())
        if "holiday_inquiry" in intent:
            context.update(await self._get_holiday_context())
        if "announcement_inquiry" in intent:
            context.update(await self._get_announcement_context())
        if "department_inquiry" in intent:
            context.update(await self._get_department_context())
        if "position_inquiry" in intent:
            context.update(await self._get_position_context())
        if "common_data_inquiry" in intent or intent == "commondata_inquiry":
            context.update(await self._get_commondata_context())
        if "leave_type_inquiry" in intent:
            context.update(await self._get_leave_type_context())
        if "employee_inquiry" in intent:
            context.update(await self._get_employee_context())
        if "handbook_inquiry" in intent:
            context.update(await self._get_handbook_context())
        if "other" in intent or not intent:
            context.update(await self._get_default_context())

        return context

    @database_sync_to_async
    def _get_leave_context(self) -> Dict[str, Any]:
        """Get leave-related context based on user role."""
        context = {}

        if self.role in ["admin", "hr"]:
            # Admin/HR can see all leave data
            context["pending_leaves"] = Leave.objects.filter(status="pending").count()
            context["total_employees"] = Users.objects.filter(role="employee").count()
            context["all_employees_leave_balances"] = (
                {
                    "employee": leave_balance.employee,
                    "year": leave_balance.year,
                    "pl_leave": leave_balance.pl,
                    "sl_leave": leave_balance.sl,
                    "lop_leave": leave_balance.lop,
                    "used_pl": leave_balance.used_pl,
                    "used_sl": leave_balance.used_sl,
                    "used_lop": leave_balance.used_lop,
                }
                for leave_balance in LeaveBalance.objects.all()
            )
            context["all_employees_leaves"] = (
                {
                    "employee": leave.employee,
                    "from_date": leave.from_date,
                    "to_date": leave.to_date,
                    "day_part": leave.day_part,
                    "is_sandwich_applied": leave.is_sandwich_applied,
                    "leave_type": leave.leave_type,
                    "status": leave.status,
                    "total_days": leave.total_days,
                    "approved_by": leave.approved_by,
                }
                for leave in Leave.objects.all()
            )

        if self.role == "employee" or self.role in ["admin", "hr"]:
            # Employee sees own data, admin/hr can see in context of specific queries
            try:
                leave_balance = LeaveBalance.objects.get(employee=self.user)
                leaves = Leave.objects.filter(employee=self.user)
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
                context["my_leaves"] = [
                    {
                        "employee": leave.employee,
                        "from_date": leave.from_date,
                        "to_date": leave.to_date,
                        "day_part": leave.day_part,
                        "is_sandwich_applied": leave.is_sandwich_applied,
                        "leave_type": leave.leave_type,
                        "status": leave.status,
                        "total_days": leave.total_days,
                        "approved_by": leave.approved_by,
                    }
                    for leave in leaves
                ]

            except LeaveBalance.DoesNotExist:
                context["my_leave_balance"] = None

        context["extra_details"] = calculate_leave_patterns()
        return context

    @database_sync_to_async
    def _get_attendance_context(self) -> Dict[str, Any]:
        """Get attendance-related context."""
        context = {}

        if self.role == "employee":
            # Employee's own attendance
            recent_attendance = EmployeeAttendance.objects.filter(
                employee=self.user
            ).order_by("-day")
            context["my_recent_attendance"] = [
                {
                    "employee": att.employee.email,
                    "day": str(att.day),
                    "status": att.status,
                    "check_in": att.check_in,
                    "check_out": att.check_out,
                    "work_hours": att.work_hours,
                    "break_hours": att.break_hours,
                    "break_logs": att.attendance_break_logs.all(),
                }
                for att in recent_attendance
            ]
        if self.role in ["admin", "hr"]:
            employees_attendance = EmployeeAttendance.objects.filter(
                employee__is_active=True
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
            context["todays_attendance"] = list(employees)
            context["all_attendances"] = list(employees_attendance)

        context["extra_details"] = calculate_attendance_patterns()
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

        context["extra_details"] = calculate_payroll_patterns()
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

        context["extra_details"] = calculate_profile_patterns()
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
        if self.role == "employee":
            context["company_stats"] = {
                "total_employees": (Users.objects.filter(role="employee").count)(),
                "total_departments": (Department.objects.count)(),
                "announcements": list(
                    Announcement.objects.values("title", "created_at")
                ),
                "leave_types": list(LeaveType.objects.values("name", "code")),
                "holidays": (list(Holiday.objects.values("name", "date"))),
            }

        context["extra_details"] = calculate_general_patterns()
        return context

    @database_sync_to_async
    def _get_holiday_context(self) -> Dict[str, Any]:
        """Get holiday-related context."""
        context = {}

        if self.role == "employee":
            context["holidays_data"] = list(
                Holiday.objects.filter(date__year=timezone.now().year).values(
                    "name", "date"
                )
            )
        elif self.role in ["admin", "hr"]:
            context["holidays_data"] = list(Holiday.objects.values("name", "date"))

        context["extra_details"] = calculate_holiday_patterns()
        return context

    @database_sync_to_async
    def _get_announcement_context(self) -> Dict[str, Any]:
        """Get announcement-related context."""
        context = {}

        if self.role == "employee":
            context["announcements_data"] = list(
                Announcement.objects.values(
                    "title", "description", "date", "created_at"
                )
            )
        elif self.role in ["admin", "hr"]:
            context["announcements_data"] = list(
                Announcement.objects.values(
                    "title", "description", "date", "created_at"
                )
            )

        context["extra_details"] = calculate_announcement_patterns()
        return context

    @database_sync_to_async
    def _get_department_context(self) -> Dict[str, Any]:
        context = {}
        context["department_data"] = list(Department.objects.values("name"))
        context["department_count"] = Department.objects.count()
        return context

    @database_sync_to_async
    def _get_position_context(self) -> Dict[str, Any]:
        context = {}
        context["position_data"] = list(Position.objects.values("name"))
        context["position_count"] = Position.objects.count()
        return context

    @database_sync_to_async
    def _get_commondata_context(self) -> Dict[str, Any]:
        context = {}
        context["common_data"] = list(
            CommonData.objects.values(
                "name",
                "company_link",
                "company_logo",
                "pl_leave",
                "sl_leave",
                "lop_leave",
                "policy_file",
                "policy_content",
                "policy_last_updated",
            )
        )
        return context

    @database_sync_to_async
    def _get_leave_type_context(self) -> Dict[str, Any]:
        context = {}
        context["leave_type_data"] = list(LeaveType.objects.values("name", "code"))
        return context

    @database_sync_to_async
    def _get_employee_context(self) -> Dict[str, Any]:
        context = {}
        if self.role == "employee":
            context["employee_data"] = list(
                Users.objects.filter(id=self.user.id).values(
                    "first_name",
                    "last_name",
                    "email",
                    "role",
                    "position__name",
                    "department__name",
                    "joining_date",
                    "birthdate",
                    "salary_ctc",
                    "profile",
                )
            )
        elif self.role in ["admin", "hr"]:
            context["employee_data"] = list(
                Users.objects.filter(role="employee").values(
                    "first_name",
                    "last_name",
                    "email",
                    "role",
                    "position__name",
                    "department__name",
                    "joining_date",
                    "birthdate",
                    "salary_ctc",
                    "profile",
                )
            )

        context["extra_details"] = calculate_employee_patterns()
        return context

    @database_sync_to_async
    def _get_handbook_context(self) -> Dict[str, Any]:
        context = {}
        context["handbook_data"] = list(
            CommonData.objects.values(
                "handbook_file",
                "handbook_content",
                "handbook_content_html",
                "handbook_last_updated",
            )
        )
        return context

    @database_sync_to_async
    def _get_default_context(self) -> Dict[str, Any]:
        """Get default context for unknown intents."""
        context = {}
        context["extra_details"] = "No specific data context available."
        return context

    def _build_prompt(self, message: str, context: Dict[str, Any], intent: str) -> str:
        """Build prompt with system context, intent-specific template, and data."""

        # Get role-specific system context
        system_context = PromptTemplates.SYSTEM_CONTEXT.get(
            self.role, PromptTemplates.SYSTEM_CONTEXT["employee"]
        )
        print(f"==>> system_context: {system_context}")

        # Get intent-specific template
        intent_template = PromptTemplates.get_template_for_intent(intent)
        print(f"==>> intent_template: {intent_template}")

        query_logs = self.get_ai_query_logs()
        handbook_data = self.get_handbook_details()
        print(f"==>> handbook_data: {handbook_data}")

        prompt = f"""
            {system_context}

            User Question: {message}

            Intent Detected: {intent}

            Instruction for this response:
            {intent_template}

            Relevant HRMS Data from Database:
            {context}

            This is handbook of HRMS company which consists data of all policies information.
            I would be needing to add that for each response, this will be having data regarding
            leave process, sandwich leave rule  and many more. So this is main reliable thing
            before anything. So carefully read and analyze its data for getting proper and good response.
            {handbook_data}

            Previous Conversation Details to know relevancy for new prompt:
            {query_logs}
            - This are previous logs, create new response learning from it.
            - Depending on user's feedback give them priority of consideration(like from 5 to 1).
            - Analyze thier intent, response time and eveything to better new responses.

            Response Guidelines:
            - Do not update timezone according to UTC.
            - Use Datetime timezone as its stored in DB only.
            - Use only the provided data, do not guess or invent information
            - After getting required context data, please rectify the need of user,
              and then show only required data or needed data to user.
            - Don't show extra data which is not asked by user.
            - If user is asking for specific data, then show only that data.
            - Don't provide extra details to user, as context is fetching some extra data normally.
            - you have to be clear which data needs to be passed and show to user accordingly.
            - Keep extra data with you only, and dont overshare then what's asked for.
            - Be concise and professional
            - Structure your response logically
            - Include specific numbers and facts when available
            - If data is unavailable, suggest checking the HRMS system directly
            - Keep responses friendly, politely but professional
            - You are an AI assistant integrated with HRMS system.
            - Your purpose is to help users with HR-related queries.
            - Always maintain professionalism and confidentiality.
            - If unsure, ask for clarification.
            - Try to respond as soon as possible, to reduce user's waiting time.
            - Always answer politely, until there's totally fucked up question from user.
            - If there's any unsual or illogical or illegal request from user then suggest user a
              proper way for that, and politely address him whatever he's suggesting is not
              right thing to do. and Hoping he will not pursue wrong ways in future.
            - If there's general_inquiry or greeting, then you should ask that you can provide a positive or
              motivational quotes if needed. can also deliver a short inspiring story if user asks for it.
            - These motivational line, quotes or short story need to be fetched by you only.
            - Here you will be getting multiple intent's, multiple context data. So please be clear afterwards
              as which data needs to setup for response and which data needs to hidden as per user's ask.
            - You have to detect in which manner, intention a user is asking. based on that, you need to answer
              properly in that context only. but our manner should polite only. But yes, you can answer in a
              smart way like humurously, frankly, joyously. this type emotions can be reflected with
              professionalism maintained.
            - Adding emojis to response would be great to have as that will enhance response attractiveness.
            - Put emojis appropriately, not too less not too much. i hope you get it.
            - After reading user's message, you need to act and respond accordingly, as many times user will ask
              irrelevant things which has nothing to do with our HRMS employee management portal.
              if anything like this occurs then you should directly refrain and explain that its a invalid request
              to process.

            - Also after generating response, add follow-up questions
              whose requirement goes like:
                1. Generate exactly 3-4 questions accordingly as you feel need.
                2. Each question should be on a new line
                3. Questions should be relevant to the user's message
                4. It should be of same intent as well.
                5. Questions should be in simple format, not complex.
                6. Numbering or bullet points.
                7. Just plain text questions, separated by new lines.
                8. Also be prepared with their answers as well. as question are being setup by us only.
                9. Dont provide answers in this response, but be prepared if user is going to ask for the same.


        """
        return prompt

    def _generate_response(
        self, message: str, context: Dict[str, Any], intent: str
    ) -> str:
        """Generate AI response based on context and intent using structured templates."""
        print(f"==>> message: {message}")
        print(f"==>> intent: {intent}")
        print(f"==>> context: {context}")

        # Build structured prompt with templates
        prompt = self._build_prompt(message, context, intent)

        try:
            llm = HuggingFaceLLM()
            response = llm.generate(prompt)
            return response
        except Exception as e:
            print("HF ERROR:", str(e))
            return "I'm having trouble generating a response right now. Please try again in a moment."

    def _generate_title_with_llm(self, message: str) -> str:
        """Generate title for user message using LLM"""
        prompt = f"""
           You are Generating a short title for user message.
           Rules:
           - Keep it short and simple
           - Summarize user's message in few words
           - No puntuation
           - No emojis
           - Title case
           - Should not exceed more than 10 words
           - No new lines or tab should be there

           User Message : {message}
        """
        print(f"==>> prompt: {prompt}")
        return prompt


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
