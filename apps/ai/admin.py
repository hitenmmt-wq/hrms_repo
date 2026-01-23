from django.contrib import admin
from django.db.models import Avg, Count
from django.urls import reverse
from django.utils.html import format_html

from apps.ai.models import AIConversation, AIMessage, AIQueryLog


@admin.register(AIConversation)
class AIConversationAdmin(admin.ModelAdmin):
    """Admin interface for AI Conversations."""

    list_display = [
        "conversation_id",
        "user_display",
        "title_display",
        "message_count",
        "is_active",
        "last_activity",
    ]
    list_filter = ["is_active", "created_at", "user__role"]
    search_fields = ["session_id", "user__email", "user__first_name", "title"]
    readonly_fields = [
        "session_id",
        "user",
        "created_at",
        "updated_at",
        "context_display",
    ]

    fieldsets = (
        ("Session Info", {"fields": ("user", "session_id", "title", "is_active")}),
        (
            "Context",
            {
                "fields": ("context_display",),
            },
        ),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def conversation_id(self, obj):
        """Display conversation ID."""
        return obj.session_id[:8] + "..."

    conversation_id.short_description = "Conversation ID"

    def user_display(self, obj):
        """Display user with link."""
        return f"{obj.user.email} ({obj.user.role.upper()})"

    user_display.short_description = "User"

    def title_display(self, obj):
        """Display conversation title."""
        return obj.title or "Untitled"

    title_display.short_description = "Title"

    def message_count(self, obj):
        """Display message count."""
        count = obj.messages.count()
        return format_html("<strong>{}</strong>", count)

    message_count.short_description = "Messages"

    def last_activity(self, obj):
        """Display last message time."""
        last_msg = obj.messages.order_by("-created_at").first()
        if last_msg:
            return last_msg.created_at.strftime("%Y-%m-%d %H:%M")
        return "No activity"

    last_activity.short_description = "Last Activity"

    def context_display(self, obj):
        """Display context data in readable format."""
        import json

        if obj.context_data:
            return format_html("<pre>{}</pre>", json.dumps(obj.context_data, indent=2))
        return "No context data"

    context_display.short_description = "Context Data"

    def has_add_permission(self, request):
        """Conversations are created automatically."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Only allow deletion by superuser."""
        return request.user.is_superuser


@admin.register(AIMessage)
class AIMessageAdmin(admin.ModelAdmin):
    """Admin interface for AI Messages."""

    list_display = [
        "message_id",
        "conversation_link",
        "message_type_display",
        "content_preview",
        "response_time_display",
        "created_at",
    ]
    list_filter = ["message_type", "created_at", "conversation__user__role"]
    search_fields = ["content", "conversation__user__email"]
    readonly_fields = [
        "conversation",
        "message_type",
        "content",
        "response_time",
        "metadata",
        "created_at",
    ]

    fieldsets = (
        ("Message Info", {"fields": ("conversation", "message_type", "content")}),
        (
            "Performance",
            {
                "fields": ("response_time",),
            },
        ),
        ("Metadata", {"fields": ("metadata",), "classes": ("collapse",)}),
        ("Timestamp", {"fields": ("created_at",), "classes": ("collapse",)}),
    )

    def message_id(self, obj):
        """Display message ID."""
        return f"#{obj.id}"

    message_id.short_description = "Message"

    def conversation_link(self, obj):
        """Display conversation link."""
        url = reverse("admin:ai_aiconversation_change", args=[obj.conversation.id])
        return format_html(
            '<a href="{}">{}</a>', url, obj.conversation.session_id[:8] + "..."
        )

    conversation_link.short_description = "Conversation"

    def message_type_display(self, obj):
        """Display message type with color."""
        colors = {
            "user": "#0066cc",
            "ai": "#00cc66",
            "system": "#ff6600",
        }
        color = colors.get(obj.message_type, "#000000")
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.message_type.upper(),
        )

    message_type_display.short_description = "Type"

    def content_preview(self, obj):
        """Display content preview."""
        content = obj.content[:50] + "..." if len(obj.content) > 50 else obj.content
        return content

    content_preview.short_description = "Content"

    def response_time_display(self, obj):
        """Display response time."""
        if obj.response_time:
            return f"{obj.response_time:.2f}s"
        return "—"

    response_time_display.short_description = "Response Time"

    def has_add_permission(self, request):
        """Messages are created automatically."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Only allow deletion by superuser."""
        return request.user.is_superuser


@admin.register(AIQueryLog)
class AIQueryLogAdmin(admin.ModelAdmin):
    """Admin interface for AI Query Logs with analytics."""

    list_display = [
        "query_id",
        "ai_message_id",
        "user_display",
        "intent_display",
        "quality_stars",
        "processing_time_display",
        "created_at",
    ]
    list_filter = ["intent", "created_at", "user__role", "response_quality"]
    search_fields = ["query", "user__email", "intent"]
    readonly_fields = [
        "user",
        "query",
        "ai_message",
        "intent",
        "data_accessed",
        "processing_time",
        "response_quality",
        "created_at",
    ]

    fieldsets = (
        ("Query Info", {"fields": ("user", "query", "intent")}),
        (
            "Performance",
            {
                "fields": ("processing_time",),
            },
        ),
        (
            "Data & Quality",
            {
                "fields": ("data_accessed", "response_quality"),
            },
        ),
        ("Timestamp", {"fields": ("created_at",), "classes": ("collapse",)}),
    )

    def query_id(self, obj):
        """Display query ID."""
        return f"#{obj.id}"

    query_id.short_description = "Query ID"

    def ai_message_id(self, obj):
        """Display AI message ID"""
        return f"#{obj.ai_message.id}"

    ai_message_id.short_description = "AI Message ID"

    def user_display(self, obj):
        """Display user with role."""
        return f"{obj.user.email} ({obj.user.role.upper()})"

    user_display.short_description = "User"

    def intent_display(self, obj):
        """Display intent with badge."""
        if obj.intent:
            colors = {
                "leave_inquiry": "#3498db",
                "attendance_inquiry": "#2ecc71",
                "payroll_inquiry": "#e74c3c",
                "profile_inquiry": "#f39c12",
                "hr_analytics": "#9b59b6",
                "company_info": "#1abc9c",
                "greeting": "#34495e",
            }
            color = colors.get(obj.intent, "#95a5a6")
            return format_html(
                '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 12px;">{}</span>',
                color,
                obj.intent.replace("_", " ").title(),
            )
        return "—"

    intent_display.short_description = "Intent"

    def quality_stars(self, obj):
        """Display response quality as stars."""
        if obj.response_quality:
            stars = "⭐" * obj.response_quality
            return format_html("{} <small>{}/5</small>", stars, obj.response_quality)
        return "—"

    quality_stars.short_description = "Quality"

    def processing_time_display(self, obj):
        """Display processing time with status."""
        if obj.processing_time:
            time_str = f"{obj.processing_time:.2f}s"
            if obj.processing_time < 2:
                color = "2ecc71"  # Green - fast
                status = "Fast"
            elif obj.processing_time < 5:
                color = "f39c12"  # Orange - acceptable
                status = "Normal"
            else:
                color = "e74c3c"  # Red - slow
                status = "Slow"
            return format_html(
                '<span style="color: {};">{} ({})</span>', color, time_str, status
            )
        return "—"

    processing_time_display.short_description = "Response Time"

    def get_queryset(self, request):
        """Filter logs based on user role."""
        qs = super().get_queryset(request)
        if request.user.is_superuser or request.user.role == "admin":
            return qs
        # Non-admin users can only see their own logs
        return qs.filter(user=request.user)

    def has_add_permission(self, request):
        """Logs are created automatically."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Only allow deletion by superuser."""
        return request.user.is_superuser

    class AISummaryAdmin(admin.AdminSite):
        """Custom admin site with AI statistics."""

        def index(self, request):
            """Display AI statistics on admin index."""
            {
                "total_conversations": AIConversation.objects.count(),
                "total_messages": AIMessage.objects.count(),
                "total_queries": AIQueryLog.objects.count(),
                "avg_response_time": AIQueryLog.objects.aggregate(
                    avg=Avg("processing_time")
                )["avg"]
                or 0,
                "avg_rating": AIQueryLog.objects.aggregate(avg=Avg("response_quality"))[
                    "avg"
                ]
                or 0,
                "total_users": AIQueryLog.objects.values("user").distinct().count(),
            }

            # Intent distribution
            (
                AIQueryLog.objects.values("intent")
                .annotate(count=Count("id"))
                .order_by("-count")[:5]
            )

            return super().index(request)


# Statistics view (optional)
class AIStatisticsAdmin(admin.ModelAdmin):
    """Display AI chatbot statistics."""

    change_list_template = "admin/ai_statistics.html"

    def changelist_view(self, request, extra_context=None):
        """Display statistics."""
        extra_context = extra_context or {}

        # Calculate statistics
        total_queries = AIQueryLog.objects.count()
        total_conversations = AIConversation.objects.count()
        total_messages = AIMessage.objects.count()

        avg_response_time = (
            AIQueryLog.objects.aggregate(avg=Avg("processing_time"))["avg"] or 0
        )

        avg_rating = (
            AIQueryLog.objects.aggregate(avg=Avg("response_quality"))["avg"] or 0
        )

        # Intent distribution
        intent_distribution = (
            AIQueryLog.objects.values("intent")
            .annotate(count=Count("id"))
            .order_by("-count")
        )

        # User distribution
        user_distribution = (
            AIQueryLog.objects.values("user__role")
            .annotate(count=Count("id"))
            .order_by("-count")
        )

        extra_context.update(
            {
                "total_queries": total_queries,
                "total_conversations": total_conversations,
                "total_messages": total_messages,
                "avg_response_time": round(avg_response_time, 2),
                "avg_rating": round(avg_rating, 2),
                "intent_distribution": intent_distribution,
                "user_distribution": user_distribution,
            }
        )

        return super().changelist_view(request, extra_context)
