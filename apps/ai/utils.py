from difflib import SequenceMatcher


class IntentClassifier:
    """Enhanced intent classification with keywords and patterns and fuzzy matching."""

    INTENT_KEYWORDS = {
        "leave_inquiry": [
            "leave",
            "vacation",
            "absent",
            "day off",
            "leave balance",
            "how many days",
            "remaining",
            "available",
            "leave application",
            "apply for leave",
            "my leaves",
            "leave status",
            "request leave",
        ],
        "attendance_inquiry": [
            "attendance",
            "present",
            "absent",
            "check-in",
            "check-out",
            "punch",
            "punctuality",
            "marking",
            "attendance report",
            "how many days present",
            "absent count",
        ],
        "payroll_inquiry": [
            "salary",
            "payslip",
            "pay",
            "payment",
            "ctc",
            "net salary",
            "gross salary",
            "deduction",
            "payout",
            "how much",
            "earning",
        ],
        "profile_inquiry": [
            "profile",
            "personal",
            "details",
            "information",
            "department",
            "position",
            "designation",
            "email",
            "phone",
            "who am i",
        ],
        "general_inquiry": [
            "birthday",
            "joining date",
            "number of employees",
            "count",
            "employee birthday" "company",
            "holiday",
            "policy",
            "department",
            "position",
            "organization",
            "structure",
            "rules",
            "procedures",
            "analytics",
            "report",
            "summary",
            "statistics",
            "trends",
            "insights",
            "data",
            "how many",
            "total",
            "average",
        ],
        "greeting": [
            "hello",
            "good morning",
            "good afternoon",
            "good evening",
            "hi",
            "good night",
            "good day",
            "hey",
            "help",
            "how are you",
            "what can you do",
            "introduce yourself",
            "greetings",
        ],
        "irrelevent": [
            "what is weather today",
            "weather",
            "gold rate",
            "silver rate",
            "global updates",
            "news",
            "love",
            "girlfriend",
            "boyfriend",
            "football",
            "cricket",
            "soccer",
            "movie",
            "song",
            "music",
            "tv",
            "show",
            "celebrity",
            "fashion",
            "travel",
            "food",
            "restaurant",
            "recipe",
            "health",
            "fitness",
            "exercise",
            "diet",
            "medical",
            "doctor",
            "hospital",
            "insurance",
            "finance",
            "stock",
            "investment",
            "banking",
            "loan",
            "credit card",
            "debit card",
            "exchange rate",
            "economy",
            "market",
            "business",
            "entrepreneurship",
            "startup",
            "career",
            "collaboration",
            "deadline",
            "news",
            "broadcast",
            "study",
            "education",
            "learning",
            "training",
            "course",
            "certification",
            "degree",
            "diploma",
            "transfer",
            "resignation",
            "termination",
            "retirement",
            "onboarding",
            "offboarding",
            "orientation",
            "conference",
            "seminar",
            "workshop",
            "training session",
            "webinar",
            "presentation",
            "showcase",
            "exhibition",
            "fair",
            "trade show",
            "convention",
            "summit",
            "forum",
            "roundtable",
            "panel discussion",
            "debate",
        ],
    }

    @classmethod
    def classify(cls, message: str) -> str:
        """Classify message intent with confidence scoring and fuzzy matching."""
        message_lower = message.lower()
        intent_scores = {}

        # Score each intent based on keyword matches (exact + fuzzy)
        for intent, keywords in cls.INTENT_KEYWORDS.items():
            score = 0
            for keyword in keywords:
                # Exact match
                if keyword in message_lower:
                    score += 1
                else:
                    # Fuzzy match for handling typos/misspellings (similarity > 0.75)
                    fuzzy_score = cls._fuzzy_match(message_lower, keyword)
                    if fuzzy_score > 0.75:
                        score += 0.5  # Lower weight for fuzzy matches
            intent_scores[intent] = score

        # Return intent with highest score
        best_intent = max(intent_scores, key=intent_scores.get)
        print(f"==>> intent_scores: {intent_scores}")

        # If no keywords matched, return general inquiry
        if intent_scores[best_intent] == 0:
            return "general_inquiry"

        return best_intent

    @classmethod
    def _fuzzy_match(cls, text: str, keyword: str, threshold: float = 0.75) -> float:
        """Perform fuzzy matching between text and keyword."""
        # Split text into words for better matching
        words = text.split()
        print(f"==>> words: {words}")
        max_ratio = 0

        # Check similarity against individual words and phrases
        for word in words:
            ratio = SequenceMatcher(None, word, keyword).ratio()
            if ratio > max_ratio:
                max_ratio = ratio

        # Also check the keyword against the full text
        ratio = SequenceMatcher(None, text, keyword).ratio()
        print(f"==>> ratio: {ratio}")
        if ratio > max_ratio:
            max_ratio = ratio

        print(f"==>> max_ratio: {max_ratio}")
        return max_ratio


class PromptTemplates:
    """Collection of prompt templates for different intents and roles."""

    SYSTEM_CONTEXT = {
        "general": """
            - You have to use timezone as stored in Database.
            - You are an AI assistant integrated with HRMS system.
            - Your purpose is to help users with HR-related queries.
            - Always maintain professionalism and confidentiality.
            - Do not make up information; only use provided data.
            - If unsure, ask for clarification.
            - If passing any data of image, then try to display image
              else dont show at all, because url_path is not ideal showing to user.
        """,
        "employee": """You are a helpful HRMS Assistant for employees.
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
            5. Use simple, non-technical language""",
        "hr": """You are an HR Assistant for HR personnel.
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
            5. Highlight important trends or issues""",
        "admin": """You are the HRMS System Administrator Assistant.
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
            5. Provide technical details when relevant""",
    }

    LEAVE_INQUIRY = """Based on the provided leave information:
        - Summarize current leave balance
        - Mention any pending applications
        - Provide recent leave history if available
        - Answer the user's specific question about leaves"""

    ATTENDANCE_INQUIRY = """Based on the provided attendance information:
        - Show recent attendance status
        - Calculate and mention attendance percentage
        - Highlight any patterns or issues
        - Answer the user's specific question about attendance"""

    PAYROLL_INQUIRY = """Based on the provided payroll information:
        - Summarize recent payslips
        - Show salary information if available
        - Mention any payment status
        - Answer the user's specific question about payroll"""

    PROFILE_INQUIRY = """Based on the provided profile information:
        - Confirm user's personal details
        - Show department and position
        - Mention employment status
        - Answer the user's specific question about their profile"""

    GENERAL_INQUIRY = """Based on the provided company information:
        - Share relevant company data and policies
        - Provide insights and statistics
        - Suggest relevant resources or procedures
        - Answer the user's specific question clearly"""

    GREETING = """Respond warmly and helpfully:
        - Greet the user appropriately
        - Brief introduction of your capabilities
        - Ask how you can help
        - Keep it friendly and professional"""

    IRRELEVENT = """
        - This are irrelevent question.
        - Questions should be avoided and tell to ask regarding HRMS portal.
        - Explain that you are not answerable to that and ask for some relevent question only.
        - Tell user to be clear with their questions.
    """

    @classmethod
    def get_template_for_intent(cls, intent: str) -> str:
        """Get the appropriate prompt template for an intent."""
        templates = {
            "leave_inquiry": cls.LEAVE_INQUIRY,
            "attendance_inquiry": cls.ATTENDANCE_INQUIRY,
            "payroll_inquiry": cls.PAYROLL_INQUIRY,
            "profile_inquiry": cls.PROFILE_INQUIRY,
            "general_inquiry": cls.GENERAL_INQUIRY,
            "greeting": cls.GREETING,
            "irrelevent": cls.IRRELEVENT,
            "hr_analytics": """Based on the provided HR data:
                - Provide comprehensive analytics
                - Highlight trends and patterns
                - Mention key metrics
                - Answer the user's specific question""",
            "company_info": """Based on the provided company information:
                - Share relevant company details
                - Provide organizational context
                - Mention policies if relevant
                - Answer the user's specific question""",
        }
        return templates.get(intent, cls.GENERAL_INQUIRY)
