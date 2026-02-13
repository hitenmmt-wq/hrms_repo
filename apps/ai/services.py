import uuid

# import ast
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
        intent = self._classify_intent(message, conversation)
        print(f"==>> intent: {intent}")
        # if isinstance(intent, str):
        #     intent = ast.literal_eval(intent)

        # Here deciding that which table to be used for CRUD
        if any(
            i.startswith("create") or i.startswith("update") or i.startswith("delete")
            for i in intent
        ):

            schema_data = await self.get_db_schema(intent)
        else:
            print("getting here -+++++++++++++++++++++++++++++++++++++++++++++++++++")
            schema_data = None
        print(f"==>> schema_data: {schema_data}")

        # intent = ('attendance_inquiry', 'payroll_inquiry', 1.297)
        context_data = await self._build_context(message, intent)
        print(f"==>> context_data: {context_data}")

        # Generate AI response (placeholder for actual AI integration)
        ai_response = self._generate_response(
            message, context_data, intent, conversation
        )

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

    # -------------------------------------------------------------------------------

    def get_db_schema(self) -> str:
        """
        Return database schema details (tables, columns, types, relations)
        formatted as LLM-friendly readable text.
        """
        from django.apps import apps

        schema_lines = []

        for model in apps.get_models():
            table_name = model._meta.db_table
            model_name = model.__name__

            schema_lines.append(f"\nTable: {table_name} (Model: {model_name})")

            for field in model._meta.get_fields():
                if hasattr(field, "attname"):
                    field_name = field.attname
                    field_type = field.get_internal_type()

                    relation = ""
                    if field.is_relation:
                        if field.many_to_one:
                            relation = " -> FK"
                        elif field.one_to_one:
                            relation = " -> OneToOne"
                        elif field.many_to_many:
                            relation = " -> M2M"

                    schema_lines.append(f"  - {field_name} ({field_type}){relation}")

        return "\n".join(schema_lines)

    async def get_auto_suggestions(self, message: str):
        """Getting Auto suggestions here for AI chatbot"""
        if message and len(message) > 5:
            auto_suggestion_prompt = self._generate_auto_suggestion_with_llm(message)
            try:
                llm = HuggingFaceLLM()
                response = llm.generate(auto_suggestion_prompt)
                auto_suggestion = response[0]
            except Exception as e:
                print("HF ERROR:", str(e))
                auto_suggestion = ""
            return auto_suggestion

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
    def get_conversation_data(self, conversation_id):
        data = AIMessage.objects.filter(conversation=conversation_id)
        return data

    @database_sync_to_async
    def get_handbook_details(self):
        data = CommonData.objects.values_list("handbook_content")
        print(f"==>> data: {data}")
        return data

    def _classify_intent(self, message: str, conversation: str) -> str:
        """Classify user intent from message."""
        message_lower = message.lower()
        print(f"==>> message_lower: {message_lower}")

        ai_query_logs = self.get_ai_query_logs()
        conversation_data = self.get_conversation_data(conversation)
        db_schema = self.get_db_schema()
        prompt = f"""
            You are an HRMS AI intent classifier.

            Your job is to identify the user's intent(s) from the message and return ONLY the
            matching intent name(s) from the list below.

            AVAILABLE INTENTS:
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
            - create_
            - update_
            - delete_

            USER MESSAGE:
            {message_lower}

            CONVERSATION HISTORY (same conversation ID):
            {conversation_data}

            PREVIOUS QUERY LOGS:
            {ai_query_logs}

            DB_SCHEMA:
            {db_schema}

            CLASSIFICATION RULES:

            CONTEXT AWARENESS:
            - Never avoid previous conversation messages while creating data as it can mislead.
              So create a thread type of linking within those messages, so it can easy to identify
              dataset-up or any problems arising there.
            - Analyze previous conversation messages to understand continuity.
            - If the current message is a follow-up (like "yes", "no", "that one", etc.), use previous intent.
            - If user continues the same topic, keep the previous intent.
            - If a new topic is added, include both old and new intents where relevant.

            MULTI-INTENT SUPPORT:
            - A message can have multiple intents.
            - Example: user asking for payroll + attendance → return both.
            - Always analyze the full message before deciding.

            CREATE ENTRY LOGIC:
            - If the user wants to apply/add/create/update/delete something in the database:
            - here prefix will be action that user wants like create, update or delete.
              and suffix will be name of the model that needs to be updated accordingly as
              per requirement.
            - This applies to cases like:
                - Apply for leave
                - Add data
                - Submit request
            - after analyzing user_message determine that which table needs to be changed.
            - Example: user asking to add Leave then intent = ['create_leave']
            - Example: user asking to update Leave then intent = ['update_leave']
            - Example: user asking to delete Leave then intent = ['delete_leave']

            SPECIAL CASES:
            - If user is greeting → return: ['greetings']
            - If intent is unclear but HR-related → return: ['general_inquiry']
            - If outside HRMS scope → return: ['other']
            - If asking about handbook/policies → return: ['handbook_inquiry']

            LEARNING FROM HISTORY:
            - Use previous logs to improve accuracy.
            - If the user is repeating the same question → keep same intent.
            - If user adds new information → merge intents accordingly.

            OUTPUT RULES (VERY STRICT):
            - Return ONLY a Python list.
            - No explanation.
            - No text before or after.
            - No reasoning.
            - Example outputs:
            ['leave_inquiry']
            ['attendance_inquiry', 'payroll_inquiry']
            ['create_']

            IMPORTANT:
            - Intent detection accuracy is critical because DB context will be fetched based on this.
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

    def _build_prompt(
        self, message: str, context: Dict[str, Any], intent: str, conversation: str
    ) -> str:
        """Build prompt using system context, intent template, HRMS data, and conversation history."""

        # Role-based system context
        system_context = PromptTemplates.SYSTEM_CONTEXT.get(
            self.role, PromptTemplates.SYSTEM_CONTEXT["employee"]
        )

        # Intent-specific instructions
        intent_template = PromptTemplates.get_template_for_intent(str(intent))

        # Additional knowledge sources
        query_logs = self.get_ai_query_logs()
        handbook_data = self.get_handbook_details()
        conversation_data = self.get_conversation_data(conversation)
        db_schema = self.get_db_schema()

        prompt = f"""
        {system_context}

        USER INPUT
        User Question: {message}
        Detected Intent: {intent}

        INTENT-SPECIFIC INSTRUCTION
        {intent_template}

        HRMS DATABASE CONTEXT
        Relevant HRMS Data:
        {context}

        Company HRMS Handbook (Policies, Leave Rules, Sandwich Leave, etc.):
        {handbook_data}

        DB SCHEMA
        This refers to database schema. and make understand the structure and
        architecture to LLM model.
        {db_schema}

        PREVIOUS LEARNING DATA
        Previous Query Logs:
        {query_logs}

        - Learn from past responses
        - Consider user feedback priority (5 to 1 scale)
        - Improve clarity, accuracy, and response quality

        CONVERSATION HISTORY
        Same Conversation Context:
        {conversation_data}

        - Use this to maintain continuity
        - Understand user's ongoing requirement
        - Avoid repeating previously provided information

        RESPONSE GUIDELINES

        ROLE & PURPOSE:
        - You are an AI assistant integrated into an HRMS system.
        - Your job is to help users with HR-related queries professionally.

        DATA USAGE RULES:
        - Use ONLY provided data. Never guess or invent.
        - Show only the information the user asked for.
        - Do not expose extra data from context.
        - Keep unused data internal.
        - If data is missing, suggest checking the HRMS system.

        TIME & DATE:
        - Do NOT convert timezone to UTC.
        - Use datetime exactly as stored in the database.

        COMMUNICATION STYLE:
        - Be concise, polite, and professional.
        - Structure responses clearly.
        - Use facts, numbers, and exact values when available.
        - Maintain confidentiality.
        - Add emojis where suitable to enhance readability.
        - Tone can be friendly, smart, or light-humorous while staying professional.

        INTENT HANDLING:
        - Detect user's intention carefully before answering.
        - If request is unrelated to HRMS → politely refuse.
        - If request is illegal/illogical → guide user toward proper action.
        - If unsure → ask for clarification.

        GENERAL INTERACTIONS:
        - For greeting/general inquiries:
        - Offer motivational quotes or short inspiring stories (only if user wants).
        - Always provide new quotes/stories; avoid repetition.

        CONTEXT AWARENESS:
        - If message belongs to same conversation:
        - Use previous user/AI messages for better understanding.
        - Maintain continuity.
        - If there's start_date and no end_date for leave or anything, then its easy
          guessing that it must be for one day only.
        - Suggest helpful next steps based on previous queries.
        (Example: suggest next month's leaves after leave inquiry.)

        USER EXPERIENCE ENHANCEMENTS:
        - Appreciate thoughtful questions.
        - Offer relevant suggestions connected to past queries.
        - Respond quickly and efficiently.

        FOLLOW-UP QUESTIONS (MANDATORY):
        After generating the response:
        - Provide exactly 3–4 follow-up questions
        - Same intent as user's query
        - Simple and relevant
        - One question per line
        - Use numbering or bullet format
        - Plain text only
        - Do NOT provide answers
        - Be prepared with answers internally

        """
        return prompt

    def _generate_response(
        self, message: str, context: Dict[str, Any], intent: str, conversation: str
    ) -> str:
        """Generate AI response based on context and intent using structured templates."""
        print(f"==>> message: {message}")
        print(f"==>> intent: {intent}")
        print(f"==>> context: {context}")

        # Build structured prompt with templates
        prompt = self._build_prompt(message, context, intent, conversation)

        try:
            llm = HuggingFaceLLM()
            response = llm.generate(prompt)
            return response
        except Exception as e:
            print("HF ERROR:", str(e))
            return "I'm having trouble generating a response right now. Please try again in a moment."

    def _generate_title_with_llm(self, message: str) -> str:
        """Generate a concise title from the user's message using LLM"""

        prompt = f"""
        You are an AI that generates a short, clean title from a user's message.

        RULES:
        - Keep it short and simple
        - Summarize the core intent of the message
        - Maximum 10 words
        - Use Title Case
        - No punctuation
        - No emojis
        - No new lines or tabs
        - Output only the title text

        User Message:
        {message}
        """
        return prompt

    def _generate_auto_suggestion_with_llm(self, message: str) -> str:
        """Generate real-time auto suggestions based on partial user input"""

        prompt = f"""
        You are an HRMS AI assistant generating real-time typing suggestions.

        CONTEXT:
        - The input is a partial message typed by the user (usually after 3+ characters).
        - Predict what the user is trying to ask.
        - Most queries will be related to HRMS topics such as:
        - Leave application / leave balance / sandwich leave
        - Attendance details
        - Holidays
        - Announcements / events / notifications
        - Payslip queries
        - Employee details
        - Department / position information
        - General HR inquiries
        - Chat-related actions

        BEHAVIOR RULES:
        - Start suggestions considering a time-based greeting (morning/afternoon/evening/night) if naturally fitting.
        - Continuously refine suggestions as the user types more characters.
        - Always generate 4–5 relevant suggestions.
        - Suggestions must be easy, clear, and HRMS-related.
        - Avoid repeating outdated suggestions when the input changes.

        STRICT OUTPUT FORMAT:
        - Return ONLY a list of suggestion strings.
        - No explanation.
        - No paragraph text.
        - No extra metadata.
        - No greeting text outside suggestions.
        - No objects, only a list of plain strings.

        Example format:
        [
        "How can I apply for leave",
        "How can I check my attendance",
        "How can I view my payslip",
        "How can I see company holidays",
        "How can I avoid sandwich leave"
        ]

        PERFORMANCE:
        - Keep suggestions concise.
        - Generate quickly for real-time UX.

        User Partial Message:
        {message}
        """
        return prompt
