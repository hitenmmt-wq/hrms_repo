import os
from datetime import datetime, timedelta
from typing import List, Optional

import django
from fastmcp import Context, FastMCP

from apps.attendance.models import EmployeeAttendance
from apps.base import constants
from apps.employee.models import LeaveBalance, PaySlip
from apps.superadmin.models import (
    Department,
    Holiday,
    Leave,
    LeaveType,
    Position,
    Users,
)

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hrms.settings")
django.setup()

# Create MCP server instance
mcp = FastMCP("hrms-tools")


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================


def _get_user_from_context(context: Context) -> Users:
    """Extract user from context or raise error."""
    user_id = context.meta.get("user_id")
    if not user_id:
        raise ValueError("No user_id in context")
    try:
        return Users.objects.get(id=user_id)
    except Users.DoesNotExist:
        raise ValueError(f"User {user_id} not found")


def _check_role(user: Users, allowed_roles: List[str]):
    """Check if user has required role."""
    if user.role not in allowed_roles:
        raise PermissionError(
            f"User role '{user.role}' not authorized. Required: {allowed_roles}"
        )


# ============================================================================
# EMPLOYEE TOOLS
# ============================================================================


@mcp.tool()
async def view_leave_balance(context: Context) -> dict:
    """View my leave balance for current year."""
    user = _get_user_from_context(context)
    _check_role(user, [constants.EMPLOYEE_USER])

    try:
        balance = LeaveBalance.objects.get(employee=user, year=datetime.now().year)
        return {
            "success": True,
            "year": balance.year,
            "privilege_leave": {
                "total": balance.pl,
                "used": balance.used_pl,
                "remaining": balance.pl - balance.used_pl,
            },
            "sick_leave": {
                "total": balance.sl,
                "used": balance.used_sl,
                "remaining": balance.sl - balance.used_sl,
            },
            "loss_of_pay": {
                "total": balance.lop,
                "used": balance.used_lop,
                "remaining": max(balance.lop - balance.used_lop, 0),
            },
        }
    except LeaveBalance.DoesNotExist:
        return {"success": False, "error": "No leave balance found for this year"}


@mcp.tool()
async def apply_leave(
    context: Context,
    leave_type: str,
    from_date: str,
    to_date: str,
    reason: str,
    half_day: Optional[bool] = False,
) -> dict:
    """Apply for leave (PL, SL, LOP). Format dates as YYYY-MM-DD."""
    user = _get_user_from_context(context)
    _check_role(user, [constants.EMPLOYEE_USER])

    try:
        # Parse dates
        from_dt = datetime.strptime(from_date, "%Y-%m-%d").date()
        to_dt = datetime.strptime(to_date, "%Y-%m-%d").date()

        # Get leave type
        ltype = LeaveType.objects.get(code=leave_type)

        # Calculate days
        total_days = (to_dt - from_dt).days + 1
        if half_day:
            total_days = 0.5

        # Create leave request
        leave = Leave.objects.create(
            employee=user,
            leave_type=ltype,
            from_date=from_dt,
            to_date=to_dt,
            total_days=total_days,
            day_part="half_day" if half_day else "full_day",
            reason=reason,
            status=constants.PENDING,
        )

        return {
            "success": True,
            "message": "Leave request submitted for approval",
            "leave_id": leave.id,
            "leave_type": leave_type,
            "from_date": str(from_dt),
            "to_date": str(to_dt),
            "days": total_days,
            "status": "PENDING",
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def check_attendance(context: Context, days: Optional[int] = 7) -> dict:
    """Check my attendance for last N days (default 7)."""
    user = _get_user_from_context(context)
    _check_role(user, [constants.EMPLOYEE_USER])

    from_date = datetime.now().date() - timedelta(days=days)
    records = EmployeeAttendance.objects.filter(
        employee=user, day__gte=from_date
    ).order_by("-day")

    attendance_list = [
        {
            "date": str(att.day),
            "status": att.status,
            "check_in": str(att.check_in) if att.check_in else None,
            "check_out": str(att.check_out) if att.check_out else None,
            "work_hours": att.work_hours or 0,
        }
        for att in records
    ]

    return {
        "success": True,
        "period_days": days,
        "total_records": len(attendance_list),
        "attendance": attendance_list,
    }


@mcp.tool()
async def view_payslip(context: Context, month: Optional[int] = None) -> dict:
    """Get payslip. If month not specified, get latest."""
    user = _get_user_from_context(context)
    _check_role(user, [constants.EMPLOYEE_USER])

    query = PaySlip.objects.filter(employee=user)
    if month:
        query = query.filter(month__icontains=str(month))

    payslip = query.order_by("-created_at").first()

    if not payslip:
        return {"success": False, "error": "No payslip found"}

    return {
        "success": True,
        "month": payslip.month,
        "basic_salary": float(payslip.basic_salary or 0),
        "allowances": {
            "hr_allowance": float(payslip.hr_allowance or 0),
            "special_allowance": float(payslip.special_allowance or 0),
        },
        "total_earnings": float(payslip.total_earnings or 0),
        "deductions": {
            "tax": float(payslip.tax_deductions or 0),
            "other": float(payslip.other_deductions or 0),
            "leave": float(payslip.leave_deductions or 0),
        },
        "total_deductions": float(payslip.total_deductions or 0),
        "net_salary": float(payslip.net_salary or 0),
    }


# ============================================================================
# HR TOOLS
# ============================================================================


@mcp.tool()
async def approve_leave(context: Context, leave_id: int, action: str) -> dict:
    """Approve or reject leave request (admin/hr only). Action: 'approve' or 'reject'."""
    user = _get_user_from_context(context)
    _check_role(user, [constants.HR_USER, constants.ADMIN_USER])

    if action not in ["approve", "reject"]:
        return {"success": False, "error": "Action must be 'approve' or 'reject'"}

    try:
        leave = Leave.objects.get(id=leave_id)
        leave.status = constants.APPROVED if action == "approve" else constants.REJECTED
        leave.approved_by = user
        leave.save()

        return {
            "success": True,
            "message": f"Leave {action}d successfully",
            "leave_id": leave_id,
            "employee": leave.employee.email,
            "status": leave.status,
        }
    except Leave.DoesNotExist:
        return {"success": False, "error": f"Leave {leave_id} not found"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def get_pending_leaves(context: Context) -> dict:
    """Get all pending leave requests (admin/hr only)."""
    user = _get_user_from_context(context)
    _check_role(user, [constants.HR_USER, constants.ADMIN_USER])

    pending = Leave.objects.filter(status=constants.PENDING).order_by("-created_at")

    leaves_list = [
        {
            "id": leave.id,
            "employee": leave.employee.email,
            "employee_name": f"{leave.employee.first_name} {leave.employee.last_name}",
            "leave_type": leave.leave_type.name,
            "from_date": str(leave.from_date),
            "to_date": str(leave.to_date),
            "days": leave.total_days,
            "reason": leave.reason,
            "applied_on": str(leave.created_at),
        }
        for leave in pending
    ]

    return {
        "success": True,
        "total_pending": len(leaves_list),
        "leaves": leaves_list,
    }


@mcp.tool()
async def view_employee_directory(context: Context) -> dict:
    """View all employees (admin/hr only)."""
    user = _get_user_from_context(context)
    _check_role(user, [constants.HR_USER, constants.ADMIN_USER])

    employees = Users.objects.filter(role=constants.EMPLOYEE_USER, is_active=True)

    emp_list = [
        {
            "id": emp.id,
            "email": emp.email,
            "name": f"{emp.first_name} {emp.last_name}",
            "employee_id": emp.employee_id,
            "department": emp.department.name if emp.department else None,
            "position": emp.position.name if emp.position else None,
            "joining_date": str(emp.joining_date) if emp.joining_date else None,
        }
        for emp in employees
    ]

    return {
        "success": True,
        "total_employees": len(emp_list),
        "employees": emp_list,
    }


# ============================================================================
# ADMIN TOOLS
# ============================================================================


@mcp.tool()
async def manage_user(
    context: Context,
    user_id: int,
    role: Optional[str] = None,
    is_active: Optional[bool] = None,
) -> dict:
    """Update user role or status (admin only)."""
    admin = _get_user_from_context(context)
    _check_role(admin, [constants.ADMIN_USER])

    try:
        user = Users.objects.get(id=user_id)

        if role:
            user.role = role
        if is_active is not None:
            user.is_active = is_active

        user.save()

        return {
            "success": True,
            "message": "User updated successfully",
            "user_id": user_id,
            "email": user.email,
            "role": user.role,
            "is_active": user.is_active,
        }
    except Users.DoesNotExist:
        return {"success": False, "error": f"User {user_id} not found"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def manage_holiday(
    context: Context, name: str, date: str, optional: Optional[bool] = False
) -> dict:
    """Create a holiday (admin only). Date format: YYYY-MM-DD."""
    admin = _get_user_from_context(context)
    _check_role(admin, [constants.ADMIN_USER])

    try:
        holiday_date = datetime.strptime(date, "%Y-%m-%d").date()

        holiday = Holiday.objects.create(
            name=name,
            date=holiday_date,
        )

        return {
            "success": True,
            "message": "Holiday created successfully",
            "holiday_id": holiday.id,
            "name": name,
            "date": str(holiday_date),
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def get_system_stats(context: Context) -> dict:
    """Get HRMS system statistics (admin only)."""
    admin = _get_user_from_context(context)
    _check_role(admin, [constants.ADMIN_USER])

    total_employees = Users.objects.filter(role=constants.EMPLOYEE_USER).count()
    total_departments = Department.objects.count()
    total_positions = Position.objects.count()
    pending_leaves = Leave.objects.filter(status=constants.PENDING).count()

    return {
        "success": True,
        "statistics": {
            "total_employees": total_employees,
            "total_departments": total_departments,
            "total_positions": total_positions,
            "pending_leaf_requests": pending_leaves,
            "active_holidays": Holiday.objects.filter(
                date__gte=datetime.now().date()
            ).count(),
        },
    }


# ============================================================================
# INFO TOOLS (Available to all)
# ============================================================================


@mcp.tool()
async def get_company_holidays(context: Context) -> dict:
    """Get upcoming company holidays."""
    holidays = Holiday.objects.filter(date__gte=datetime.now().date()).order_by("date")

    holidays_list = [
        {
            "name": h.name,
            "date": str(h.date),
        }
        for h in holidays
    ]

    return {
        "success": True,
        "total": len(holidays_list),
        "holidays": holidays_list,
    }


@mcp.tool()
async def get_my_profile(context: Context) -> dict:
    """Get my profile information."""
    user = _get_user_from_context(context)

    return {
        "success": True,
        "profile": {
            "email": user.email,
            "name": f"{user.first_name} {user.last_name}",
            "role": user.role,
            "employee_id": user.employee_id,
            "department": user.department.name if user.department else None,
            "position": user.position.name if user.position else None,
            "joining_date": str(user.joining_date) if user.joining_date else None,
            "salary_ctc": float(user.salary_ctc or 0),
        },
    }


# Here create more such tools for different tables as per requirement.


# ============================================================================
# SERVER STARTUP
# ============================================================================


def create_mcp_server():
    """Create and return the FastMCP server instance."""
    return mcp


if __name__ == "__main__":
    # Run as standalone server
    print("🚀 Starting HRMS FastMCP Server...")
    print("Listen for connections from Claude or MCP clients")
    mcp.run()
