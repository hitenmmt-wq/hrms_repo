"""
Application-wide constants for HRMS system.

Defines all constant values used across the HRMS application including
user roles, status values, notification types, and leave types for
consistent reference throughout the codebase.
"""

ACCOUNT_ACTIVATION_URL = (
    "https://crystal-papers-rack-marking.trycloudflare.com/superadmin/activate/{token}/"
)

LOCALHOST = "http://127.0.0.1:8000/"
LIVE_SERVER = "https://crystal-papers-rack-marking.trycloudflare.com/"

# USER ROLE CONSTANTS
ADMIN_USER = "admin"
EMPLOYEE_USER = "employee"
HR_USER = "hr"

# STATUS CONSTANTS
APPROVED = "approved"
REJECTED = "rejected"
PENDING = "pending"
PRESENT = "present"
INCOMPLETE_HOURS = "incomplete_hours"

# NOTIFICATION CONSTANTS
LEAVE_APPLY = "leave_apply"
PAYSLIP_GENERATED = "payslip_generated"

PRIVILEGE_LEAVE = "privilege"
SICK_LEAVE = "sick"
OTHER_LEAVE = "other"

ANNOUNCEMENT_NOTIFY = "announcement"
CHAT_NOTIFY = "chat_message"
ATTENDANCE_REMINDER = "attendance_reminder"
ATTENDANCE_REJECTED = "attendance_rejected"

# LEAVE_TYPE CONSTANTS
UNPAID_LEAVE = "unpaid_leave"
PAID_LEAVE = "paid_leave"
HALFDAY_LEAVE = "halfday_leave"

BIRTHDAY = "birthday"

LATE_COMING = "late_coming"

NEXT_DAY_HOLIDAY = "holiday"

NOTIFICATION_URL_MAP_ADMIN = {
    CHAT_NOTIFY: "/chat",
    LEAVE_APPLY: "/leaveapproval",
    ANNOUNCEMENT_NOTIFY: "/common-data/announcement",
    ATTENDANCE_REMINDER: "/attendance",
    ATTENDANCE_REJECTED: "/attendance",
    LATE_COMING: "/attendance",
    PAYSLIP_GENERATED: "/payslip",
    NEXT_DAY_HOLIDAY: "/common-data/holiday",
}

NOTIFICATION_URL_MAP = {
    CHAT_NOTIFY: "/chat",
    LEAVE_APPLY: "/leave",
    ANNOUNCEMENT_NOTIFY: "/announcements",
    ATTENDANCE_REMINDER: "/my-attendance",
    ATTENDANCE_REJECTED: "/my-attendance",
    LATE_COMING: "/my-attendance",
    PAYSLIP_GENERATED: "/my-payslips",
    NEXT_DAY_HOLIDAY: "/common-data/holiday",
}
