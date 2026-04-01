"""
MCP Tools Integration Layer - Bridges FastMCP server with AI services.

This module provides wrapper classes that enable the AI service to execute
role-based MCP tools for querying and manipulating HRMS data.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from apps.base import constants
from apps.superadmin.models import Holiday, Leave, Users

logger = logging.getLogger(__name__)


class RoleBasedMCPTools:
    """
    Wrapper around FastMCP tools that provides role-based access control.

    This class exposes FastMCP tools as methods, automatically enforcing
    role-based permissions and handling tool execution with user context.
    """

    # Available tools mapped by role
    ROLE_TOOLS_MAP = {
        constants.EMPLOYEE_USER: [
            "view_leave_balance",
            "apply_leave",
            "check_attendance",
            "view_payslip",
            "get_company_holidays",
            "get_my_profile",
        ],
        constants.HR_USER: [
            "approve_leave",
            "get_pending_leaves",
            "view_employee_directory",
            "get_company_holidays",
            "get_my_profile",
        ],
        constants.ADMIN_USER: [
            "manage_user",
            "manage_holiday",
            "get_system_stats",
            "approve_leave",
            "get_pending_leaves",
            "view_employee_directory",
            "get_company_holidays",
            "get_my_profile",
        ],
    }

    def __init__(self):
        """Initialize MCP tools wrapper."""
        self.mcp_server = None
        self._load_mcp_server()

    def _load_mcp_server(self):
        """Lazy load the FastMCP server."""
        try:
            from apps.ai.fastmcp_server import mcp as mcp_server

            self.mcp_server = mcp_server
        except Exception as e:
            logger.warning(f"Failed to load FastMCP server: {str(e)}")

    def get_available_tools(self, user: Users) -> List[str]:
        """
        Get list of tools available for a specific user role.

        Args:
            user: User object with role attribute

        Returns:
            List of tool names available to the user
        """
        return self.ROLE_TOOLS_MAP.get(user.role, [])

    def can_use_tool(self, user: Users, tool_name: str) -> bool:
        """
        Check if user can use a specific tool.

        Args:
            user: User object with role attribute
            tool_name: Name of the tool to check

        Returns:
            True if user can use the tool, False otherwise
        """
        available_tools = self.get_available_tools(user)
        return tool_name in available_tools

    async def execute_tool(
        self, user: Users, tool_name: str, **kwargs
    ) -> Dict[str, Any]:
        """
        Execute an MCP tool with user role verification.

        Args:
            user: User object for context and role verification
            tool_name: Name of the tool to execute
            **kwargs: Tool-specific parameters

        Returns:
            Tool execution result as dictionary
        """
        # Check permissions
        if not self.can_use_tool(user, tool_name):
            return {
                "success": False,
                "error": f"User role '{user.role}' not authorized to use tool '{tool_name}'",
            }

        try:
            # Create context for tool execution
            context = self._create_context(user, kwargs)

            # Get tool from MCP server and execute
            if self.mcp_server and hasattr(self.mcp_server, "tools"):
                tool_func = self._get_tool_function(tool_name)

                if not tool_func:
                    return {
                        "success": False,
                        "error": f"Tool '{tool_name}' not found in MCP server",
                    }

                # Execute tool asynchronously
                if asyncio.iscoroutinefunction(tool_func):
                    result = await tool_func(context, **kwargs)
                else:
                    result = tool_func(context, **kwargs)

                return result
            else:
                logger.warning("FastMCP server not loaded")
                # Fallback: execute tool-specific logic directly
                return await self._execute_tool_direct(user, tool_name, **kwargs)

        except Exception as e:
            logger.error(f"Error executing tool '{tool_name}': {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": f"Error executing tool: {str(e)}",
            }

    def _get_tool_function(self, tool_name: str):
        """Get tool function from MCP server."""
        try:
            # Tools are registered in fastmcp_server.py with @mcp.tool() decorator
            if hasattr(self.mcp_server, tool_name):
                return getattr(self.mcp_server, tool_name)
            return None
        except Exception as e:
            logger.error(f"Error getting tool function '{tool_name}': {str(e)}")
            return None

    def _create_context(self, user: Users, kwargs: Dict) -> Dict[str, Any]:
        """
        Create context object for tool execution.

        Args:
            user: User object
            kwargs: Additional kwargs passed to tool

        Returns:
            Context dictionary for tool execution
        """

        # Simple context class replacement
        class Context:
            def __init__(self, user_id):
                self.meta = {"user_id": user_id}

        return Context(user.id)

    async def _execute_tool_direct(
        self, user: Users, tool_name: str, **kwargs
    ) -> Dict[str, Any]:
        """
        Execute tool directly without MCP server (fallback).
        This provides basic tool execution when MCP server is not loaded.

        Args:
            user: User making the request
            tool_name: Name of the tool to execute
            **kwargs: Tool parameters

        Returns:
            Tool execution result
        """
        # Import models for direct execution
        from datetime import datetime, timedelta

        from apps.attendance.models import EmployeeAttendance
        from apps.employee.models import LeaveBalance, PaySlip

        try:
            # Employee tools
            if tool_name == "view_leave_balance":
                balance = LeaveBalance.objects.get(
                    employee=user, year=datetime.now().year
                )
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
                }

            elif tool_name == "check_attendance":
                days = kwargs.get("days", 7)
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
                    }
                    for att in records
                ]

                return {
                    "success": True,
                    "period_days": days,
                    "total_records": len(attendance_list),
                    "attendance": attendance_list,
                }

            elif tool_name == "view_payslip":
                month = kwargs.get("month")
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
                    "net_salary": float(payslip.net_salary or 0),
                }

            elif tool_name == "get_company_holidays":
                holidays = Holiday.objects.filter(
                    date__gte=datetime.now().date()
                ).order_by("date")

                holidays_list = [
                    {"name": h.name, "date": str(h.date)} for h in holidays
                ]

                return {
                    "success": True,
                    "total": len(holidays_list),
                    "holidays": holidays_list,
                }

            elif tool_name == "get_my_profile":
                return {
                    "success": True,
                    "profile": {
                        "email": user.email,
                        "name": f"{user.first_name} {user.last_name}",
                        "role": user.role,
                        "department": user.department.name if user.department else None,
                        "position": user.position.name if user.position else None,
                    },
                }

            # HR tools
            elif tool_name == "get_pending_leaves":
                pending = Leave.objects.filter(status=constants.PENDING).order_by(
                    "-created_at"
                )
                leaves_list = [
                    {
                        "id": leave.id,
                        "employee": leave.employee.email,
                        "leave_type": leave.leave_type.name,
                        "from_date": str(leave.from_date),
                        "to_date": str(leave.to_date),
                    }
                    for leave in pending
                ]

                return {
                    "success": True,
                    "total_pending": len(leaves_list),
                    "leaves": leaves_list,
                }

            else:
                return {
                    "success": False,
                    "error": f"Tool '{tool_name}' not implemented in direct execution",
                }

        except Exception as e:
            logger.error(f"Error in direct tool execution: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": f"Error executing tool: {str(e)}",
            }


class TaskExecutor:
    """
    Executor for AI-generated tasks using MCP tools.

    This class takes AI-identified tasks and executes them through
    the appropriate MCP tools with proper role-based access control.
    """

    def __init__(self, user: Users, mcp_tools: RoleBasedMCPTools):
        """
        Initialize task executor.

        Args:
            user: User object for execution context
            mcp_tools: RoleBasedMCPTools instance for tool execution
        """
        self.user = user
        self.mcp_tools = mcp_tools

    async def execute_task(
        self, task_name: str, task_params: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Execute a specific task through MCP tools.

        Args:
            task_name: Name of the task to execute
            task_params: Parameters for the task

        Returns:
            Task execution result
        """
        task_params = task_params or {}

        logger.info(f"Executing task '{task_name}' for user {self.user.email}")

        try:
            # Map task names to MCP tool names
            tool_name = self._map_task_to_tool(task_name)

            if not tool_name:
                return {
                    "success": False,
                    "error": f"No MCP tool mapped for task '{task_name}'",
                }

            # Execute the tool through MCP tools
            result = await self.mcp_tools.execute_tool(
                self.user, tool_name, **task_params
            )

            return result

        except Exception as e:
            logger.error(f"Error executing task '{task_name}': {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": f"Task execution error: {str(e)}",
            }

    def _map_task_to_tool(self, task_name: str) -> Optional[str]:
        """
        Map AI task name to MCP tool name.
        Args:
            task_name: Task name from AI
        Returns:
            Corresponding MCP tool name or None if not found
        """
        # Task to tool mapping
        task_tool_map = {
            "check_my_leaves": "view_leave_balance",
            "apply_for_leave": "apply_leave",
            "check_attendance": "check_attendance",
            "get_payslip": "view_payslip",
            "get_holidays": "get_company_holidays",
            "get_profile": "get_my_profile",
            "pending_leaves": "get_pending_leaves",
            "employees": "view_employee_directory",
            "system_stats": "get_system_stats",
        }

        return task_tool_map.get(task_name)

    def get_available_tasks(self) -> List[str]:
        """
        Get list of tasks available for current user.

        Returns:
            List of available task names
        """
        available_tools = self.mcp_tools.get_available_tools(self.user)

        # Map tools back to task names for user-friendly display
        tool_task_map = {
            v: k
            for k, v in {
                "check_my_leaves": "view_leave_balance",
                "apply_for_leave": "apply_leave",
                "check_attendance": "check_attendance",
                "get_payslip": "view_payslip",
                "get_holidays": "get_company_holidays",
                "get_profile": "get_my_profile",
                "pending_leaves": "get_pending_leaves",
            }.items()
        }

        available_tasks = [tool_task_map.get(tool, tool) for tool in available_tools]

        return available_tasks
