"""
Application-wide constants for HRMS system.

Defines all constant values used across the HRMS application including
user roles, status values, notification types, and leave types for
consistent reference throughout the codebase.
"""

ACCOUNT_ACTIVATION_URL = "https://insights-photo-includes-nursing.trycloudflare.com/superadmin/activate/{token}/"

LOCALHOST = "http://127.0.0.1:8000/"
LIVE_SERVER = "https://insights-photo-includes-nursing.trycloudflare.com/"

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
