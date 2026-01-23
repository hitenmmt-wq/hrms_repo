class IntentClassifier:
    """Enhanced intent classification with keywords and patterns."""

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
            "company",
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
    }

    @classmethod
    def classify(cls, message: str) -> str:
        """Classify message intent with confidence scoring."""
        message_lower = message.lower()
        intent_scores = {}

        # Score each intent based on keyword matches
        for intent, keywords in cls.INTENT_KEYWORDS.items():
            score = sum(1 for keyword in keywords if keyword in message_lower)
            intent_scores[intent] = score

        # Return intent with highest score
        best_intent = max(intent_scores, key=intent_scores.get)
        print(f"==>> intent_scores: {intent_scores}")

        # If no keywords matched, return general inquiry
        if intent_scores[best_intent] == 0:
            return "general_inquiry"

        return best_intent

    @classmethod
    def get_intent_description(cls, intent: str) -> str:
        """Get human-readable description of intent."""
        descriptions = {
            "leave_inquiry": "Leave Balance & Applications",
            "attendance_inquiry": "Attendance Records",
            "payroll_inquiry": "Salary & Payslips",
            "profile_inquiry": "Personal Profile",
            "hr_analytics": "HR Analytics & Reports",
            "company_info": "Company Information",
            "greeting": "Greeting",
            "general_inquiry": "General Question",
        }
        return descriptions.get(intent, intent)
