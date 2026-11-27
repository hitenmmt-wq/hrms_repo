# HRMS Project Guide

This guide explains the Human Resource Management System (HRMS) in everyday
language. It is intended for someone who is new to the project and wants to
understand what the system does, who uses it, and how its parts work together.

For the complete HTTP and WebSocket endpoint catalogue, see
[API_REFERENCE.md](./API_REFERENCE.md).

## 1. What this project is

HRMS is an internal web application for managing employee and HR work in one
place. A person uses the React website in a browser. The website sends requests
to a Django server. Django validates those requests and reads or updates records
in a PostgreSQL database.

The application includes:

- Employee accounts and profiles
- Attendance and break tracking
- Leave requests, balances, and approval
- Payroll records and downloadable payslips
- Company announcements, holidays, departments, and positions
- Internal conversations, files, read receipts, and reactions
- Notifications
- An AI assistant for HR-related questions and supported actions
- Supporting areas for tickets, expenses, inventory, projects, and daily
  reports

Some endpoints and data models are broader than the screens currently exposed
in the frontend. The backend API catalogue documents both the user-facing and
additional backend endpoints.

## 2. Who uses it

### Administrator (`admin`)

An administrator maintains the organisation's HR data and oversees employee
activity. The current frontend provides administrator screens for employee
management, attendance, leave approval, payslips, announcements, and shared
configuration.

Typical administrator work:

1. Set up company information, departments, positions, leave types, holidays,
   and announcements.
2. Create and maintain employee accounts.
3. Review attendance and leave activity.
4. Approve or reject leave requests.
5. Prepare payroll and provide payslips.
6. Use chat and notifications to communicate with employees.

Some server permission rules let any signed-in user read certain resources,
while only administrators can change them. The exact rule for each API area is
described in [API_REFERENCE.md](./API_REFERENCE.md).

### Employee (`employee`)

An employee uses the system for their own day-to-day HR tasks:

1. Sign in and view their employee dashboard.
2. Check in, pause for a break, resume work, and check out.
3. Review leave balances and submit leave requests.
4. Check leave request status and read company announcements and holidays.
5. View and download payslips.
6. Chat with other participants and receive notifications.

### HR role

The backend contains an `hr` role permission helper, and AI analytics includes
special handling for `hr`. However, the current frontend routes and dashboards
are primarily built around `admin` and `employee`. Do not assume that `hr` has
a complete separate user interface or a consistent set of HR-only permissions.

### Device/desktop client

There are endpoints for registering an employee's device and obtaining device
configuration. The device client uses a tracking token for its configuration
and activity requests. These are separate from the normal browser login flow.

## 3. Main user workflows

### Employee account and sign-in

An account is identified by its email address. After successful sign-in, the
server returns a short-lived access token and a refresh token. The frontend
sends the access token on protected API requests using:

```http
Authorization: Bearer <access-token>
```

The user's role is included in the login response and access-token payload so
the frontend can choose the relevant dashboard and navigation items.

### Attendance

The employee starts a daily attendance record by checking in. They may pause
and resume the work session to record breaks, then check out. The server
calculates work and break time and keeps a daily record. Administrators can
review attendance records, while employees use their own attendance screens.

The calendar endpoint combines attendance records with holidays and weekends
for a requested employee and month.

### Leave

An employee submits a leave type, date range, and reason. A single-day or
half-day request is represented using the corresponding dates and `day_part`.
The backend calculates leave duration; the leave model also supports a
weekend/holiday "sandwich" calculation when applicable.

An administrator reviews requests and approves or rejects them. Approval
records who responded, updates leave balances, creates attendance entries for
the leave dates, and triggers a notification. Employees can view their leave
history and cancel requests that have not already been approved.

### Payslips and payroll

Administrators can create or maintain payslip records. Standard payslip
creation calculates earnings, leave deductions, total deductions, and net pay
from the submitted salary components and date range. There are also manual
calculation/generation endpoints. Employees can request their payslip list and
download a payslip PDF.

Celery Beat schedules background work such as monthly payslip generation,
attendance automation, leave balance updates, and employee notifications. See
the schedule in `backend/hrms/celery.py` for the current tasks and times.

### Chat and notifications

Users can create private or group conversations, list their conversations,
retrieve messages, and upload supported files. WebSockets provide real-time
message updates, typing status, read status, reactions, and group membership
events.

Notification records can be read through HTTP endpoints. A notification
WebSocket pushes live updates to the signed-in user. Browser push-token
registration is also available for clients that use Firebase Cloud Messaging.
Birthday......

### AI assistant

The AI assistant stores conversations and their messages for each user. It can
answer HRMS questions, use role-aware data context, expose available tools, and
execute supported tasks. HTTP endpoints provide conversation history, message
sending, quick questions, tool listing/execution, and analytics. The AI chat
also has a WebSocket interface.

The AI functions depend on the configured provider and related environment
settings. A successful app startup alone does not mean an external AI provider
has been configured.

## 4. How the software is organised

```text
Browser
  React + Vite frontend
       | HTTP/JSON and WebSocket
       v
  Django + Django REST Framework + Django Channels
       |                          |
       v                          v
  PostgreSQL                 Redis
                                  |
                                  v
                              Celery worker
                              Celery Beat
```

- **Frontend (`frontend/`)**: React pages, reusable components, Redux state,
  API clients, and WebSocket clients. Vite builds and serves the frontend.
- **Backend (`backend/hrms/`)**: Django project settings, root URL routes,
  ASGI/WebSocket routing, and Celery configuration.
- **Backend apps (`backend/apps/`)**: Feature-specific code, including
  `superadmin`, `employee`, `attendance`, `chat`, `notification`, `ai`, and
  shared `base` utilities.
- **PostgreSQL**: Stores accounts, leave, attendance, payroll, chat, and other
  business records.
- **Redis**: Used by Channels for live events and by Celery as a task broker
  and result backend, depending on environment configuration.
- **Celery worker**: Runs background jobs outside the request/response cycle.
- **Celery Beat**: Schedules recurring background jobs.
- **Daphne**: ASGI server for HTTP and WebSocket traffic.
- **Nginx**: Reverse proxy in the Compose configuration.

### What happens when a person uses the website

1. The browser loads the React frontend.
2. React makes an HTTP request to a Django endpoint, or opens a WebSocket for
   live communication.
3. Django checks the request, its authentication, permissions, and input.
4. Django reads or writes PostgreSQL data and returns JSON, a file, or a
   WebSocket event.
5. Longer or scheduled work can be handed to Celery and processed separately.

## 5. Important data concepts

- **User**: A person who can sign in. The account has an email, role, employee
  details, and optional department, position, and profile image.
- **Department and position**: Organisation-wide lookup records associated
  with employees.
- **Leave type and leave balance**: A leave type describes a category of
  leave; a yearly balance tracks allocated and used amounts.
- **Attendance**: One employee's work record for a day, including check-in,
  check-out, breaks, status, and hours.
- **Payslip**: A payroll period and its earnings, deductions, and net salary.
- **Conversation and message**: A private or group chat and its messages.
- **Notification**: An alert assigned to a recipient, with a read/unread state.
- **Base records**: Many backend records inherit timestamps and soft-delete
  fields. A normal delete may hide a record instead of permanently removing
  it; some models do not use this base behavior.

## 6. Frontend pages

The frontend's main routes include:

- Public: `/login`, `/signup`, `/forgot-password`, `/reset-password`
- Shared signed-in pages: dashboard (`/`), `/chat`, `/profile`,
  `/notifications`
- Administrator pages: `/employees`, `/attendance`, `/leaveapproval`,
  `/payroll`, `/payslip`, `/permissions`, and the `/common-data/...` pages
- Employee pages: `/my-attendance`, `/leave`, `/my-payslips`,
  `/announcements`, `/holidays`

The frontend route guard improves navigation and user experience; it is not a
replacement for server-side API permissions. Always use the backend permission
rules as the authority for access.

## 7. Operational notes

- Development API paths are rooted directly at the backend host; they do not
  all start with `/api/`. For example, login is
  `/superadmin/auth/login/`.
- The backend Docker Compose file is under `backend/`. Check that file and the
  environment examples to see which services your current setup runs.
- Do not put database passwords, Django secret keys, Firebase private
  credentials, or other secrets in these documentation files or commit them.
- Local environment files such as `backend/.env`, `backend/.env.docker`, and
  `frontend/.env` are configuration inputs, not documentation examples.
- Current backend API reference: [API_REFERENCE.md](./API_REFERENCE.md).
- Interactive API documentation is served by Django at
  `/api/schema/swagger-ui/` and `/api/schema/redoc/` when the backend is
  running. The OpenAPI schema is at `/api/schema/`.
