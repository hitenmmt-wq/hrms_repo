# HRMS API Reference

This is a route-level reference for the HTTP API and WebSocket endpoints
registered by the current Django code. It lists paths, methods, purpose,
authentication expectations, and important request fields. The backend source
and its serializers remain authoritative if behavior changes.

## 1. Base URL and request conventions

Use the backend origin as the base URL. For the common local setup:

```text
http://localhost:8000
```

Paths below are relative to that origin. The application does **not** put every
endpoint under an `/api/` prefix.

### Authentication

Protected HTTP routes use a SimpleJWT access token:

```http
Authorization: Bearer <access-token>
Content-Type: application/json
```

The configured access token lifetime is one day; refresh token lifetime is
seven days. A few endpoints are intentionally public or use a device tracking
token instead. Endpoint groups below describe those differences.

### Responses and pagination

- Standard CRUD endpoints may return a normal serializer body, an
  `ApiResponse` wrapper, or a paginated response. Response shapes are not
  perfectly uniform across the codebase.
- Paginated endpoints use page-number pagination, normally with
  `page` (default page size 10) and `page_size` (maximum 100).
- Where a view supports them, list filters commonly include `search` and
  `ordering`; each resource has its own filter fields.
- Dates are generally sent as `YYYY-MM-DD`. Datetimes are timezone-aware.
- For file uploads, use `multipart/form-data`.

### Access rule shorthand

- **Authenticated**: any signed-in user, unless the endpoint adds a narrower
  rule.
- **Admin write**: the backend `IsAdmin` permission allows authenticated
  users to perform safe/read methods, but only users with role `admin` to
  perform writes.
- **Public**: no explicit authentication requirement is set on that view.
- **Tracking token**: uses a device token in the request, not the normal
  bearer-token login flow.

The backend's global REST framework default permission is `AllowAny`. An
endpoint without an explicit permission class is therefore public unless
other code checks authentication itself. See the important access notes in
section 7.

## 2. Authentication and account endpoints

| Method | Path | Access | Purpose and request fields |
|---|---|---|---|
| `POST` | `/superadmin/auth/login/` | Public | Sign in with `email` and `password`. Returns `access`, `refresh`, and a `user` object containing identity and role data. |
| `POST` | `/superadmin/auth/token/refresh/` | Public | Refresh an access token. Body: `{"refresh":"<refresh-token>"}`. |
| `GET` | `/superadmin/auth/token/user/` | Authenticated | Return the current user's basic profile. |
| `POST` | `/superadmin/auth/change_password/` | Authenticated | Body: `old_password`, `new_password`, `confirm_new_pass`. |
| `POST` | `/superadmin/auth/reset_password/` | Public | Request a reset email. Body: `email`. |
| `POST` | `/superadmin/auth/confirm_reset_password/` | Public | Complete reset. Body: `uid`, `token`, `new_password`, `confirm_password`. |
| `GET` | `/superadmin/admin_dashboard/` | Admin write rule (read endpoint) | Administrator dashboard summary. |
| `GET` | `/employee/employee_dashboard/` | Authenticated | Current employee dashboard summary. |
| `GET` | `/superadmin/custom_script/` | Public by configured permission default | Custom script/data endpoint. See access note in section 7. |

## 3. Standard CRUD route patterns

The following resources are registered with Django REST Framework routers.
Unless a resource-specific note below says otherwise, these methods are
available:

| Method | Collection/detail route | Meaning |
|---|---|---|
| `GET` | `/<collection>/` | List records |
| `POST` | `/<collection>/` | Create a record |
| `GET` | `/<collection>/<id>/` | Retrieve one record |
| `PUT` | `/<collection>/<id>/` | Replace/update a record |
| `PATCH` | `/<collection>/<id>/` | Partially update a record |
| `DELETE` | `/<collection>/<id>/` | Delete a record; for models using the shared base model this is normally a soft delete |

For `BaseViewSet` resources, these additional routes are registered:

| Method | Route | Meaning |
|---|---|---|
| `GET` | `/<collection>/complete_list/` | List all records, including soft-deleted records |
| `GET` | `/<collection>/deleted_data_list/` | List soft-deleted records |
| `POST` | `/<collection>/<id>/restore/` | Restore a soft-deleted record |
| `DELETE` | `/<collection>/<id>/force_delete/` | Permanently delete a record |

The last four actions depend on model support for the shared `all_objects`,
`restore()`, and `force_delete()` behavior. Not every model in this project
inherits the shared soft-delete model; check a resource's model before relying
on these operations.

### Resource inventory

The base above applies to these collection paths. The access label is based on
the permission class in the view, not just on which frontend screen links to
the resource.

| Collection path | Access | Data |
|---|---|---|
| `/superadmin/admin_register/` | No explicit permission; see section 7 | Administrator-account management |
| `/superadmin/common_data/` | Admin write rule | Company profile, leave defaults, policy and handbook |
| `/superadmin/setting_data/` | Admin write rule | Email, database, timezone, token, and task settings |
| `/superadmin/holiday/` | Admin write rule | Company holidays |
| `/superadmin/department/` | Admin write rule | Departments |
| `/superadmin/announcement/` | Admin write rule | Company announcements |
| `/superadmin/position/` | Admin write rule | Job positions |
| `/superadmin/profile/` | Authenticated | User profile records |
| `/superadmin/leave/` | Authenticated; list scope differs by role | Leave requests |
| `/superadmin/leave_type/` | Admin write rule | Leave categories (the unpaid leave category is excluded from this queryset) |
| `/superadmin/client/` | Admin write rule | Clients |
| `/superadmin/project/` | Admin write rule | Projects |
| `/superadmin/daily_report/` | Authenticated | Employee daily reports |
| `/employee/employee/` | Admin write rule | Active employee accounts |
| `/employee/leave_balance/` | Admin write rule | Yearly employee leave balances |
| `/employee/apply_leave/` | Authenticated | Leave application workflow |
| `/employee/pay_slip/` | Admin write rule | Payslip records and payroll actions |
| `/employee/ticket_issue/` | Authenticated | Support tickets |
| `/employee/item/` | Authenticated | Inventory item catalogue |
| `/employee/inventory_detail/` | Authenticated | Individual inventory assets/serial numbers |
| `/employee/item_assignment/` | Authenticated | Asset assignments |
| `/employee/item_history/` | Authenticated | Asset action history |
| `/employee/expense_claim/` | Authenticated | Expense claims |
| `/attendance/employee_attendance/` | Authenticated | Attendance records and time-tracking actions |
| `/notify/notification_type/` | Admin write rule | Notification categories |
| `/notify/notifications/` | Admin write rule for CRUD; some actions allow any authenticated user | Notifications addressed to the current user |
| `/ai/conversations/` | Authenticated; records scoped to current user | AI assistant conversations |
| `/ai/analytics/` | Authenticated; query-log scope differs by role | AI query logs and analytics |

**Router detail identifier:** `{id}` is the database primary key. Routes ending
in a slash are canonical.

## 4. Resource-specific actions and standalone routes

### Employees

| Method | Path | Access | Details |
|---|---|---|---|
| `GET` | `/employee/employee/present_employees/` | Admin write rule (read endpoint) | Employees with a check-in record today. |
| `GET` | `/employee/employee/absent_employees/` | Admin write rule (read endpoint) | Active employees without a check-in record today. |
| `POST` | `/employee/employee/activate_employee/` | Admin | Body: `employee_id`. |
| `POST` | `/employee/employee/deactivate_employee/` | Admin | Body: `employee_id`. |

Employee creation uses fields including `first_name`, `last_name`, `email`,
`role`, `department`, `position`, `employee_id`, `password`, `joining_date`,
`birthdate`, and `salary_ctc`. Department and position are database IDs.

### Leave

| Method | Path | Access | Details |
|---|---|---|---|
| `GET` | `/employee/apply_leave/employee_leave_list/` | Authenticated | Current user's leave history. |
| `POST` | `/superadmin/leave/{id}/approve/` | Admin | Approve a request; optional body field `response_text`. |
| `POST` | `/superadmin/leave/{id}/reject/` | Admin | Reject a request; optional body field `response_text`. |
| `GET` | `/superadmin/leave_balance_details/` | Authenticated | Requires `employee_id`, `start_date`, and `end_date`. The current view reads these from the request body despite using `GET`; a GET body is not reliably supported by all clients. |
| `POST` | `/superadmin/leave/{id}/cancel/` | Authenticated owner | Cancel own leave if it is not already approved. |

For leave application creation, send `leave_type` (ID), `from_date`,
`to_date`, `reason`, and optional `day_part`. The employee is taken from the
signed-in user by `/superadmin/leave/`; `/employee/apply_leave/` has its own
create serializer and accepts an `employee` ID field. Prefer the
`/superadmin/leave/` create route for a self-service application because it
sets the employee from the authenticated account.

### Attendance

| Method | Path | Access | Details |
|---|---|---|---|
| `POST` | `/attendance/employee_attendance/check_in/` | Authenticated | Check in the current user for today. |
| `GET` | `/attendance/employee_attendance/daily_logs/` | Authenticated | Break logs for the current user's attendance today. |
| `GET` | `/attendance/employee_attendance/{id}/particular_employee/` | Authenticated | Attendance history for the employee whose ID is supplied as `{id}`. |
| `POST` | `/attendance/employee_attendance/{id}/pause/` | Authenticated | Start a break on the specified attendance record. |
| `POST` | `/attendance/employee_attendance/{id}/resume/` | Authenticated | End the active break. |
| `POST` | `/attendance/employee_attendance/{id}/check_out/` | Authenticated | Check out the specified attendance record. |
| `GET` | `/attendance/employee_attendance/get_attendance_summary/?attendance_id={id}` | Authenticated | Fetch one attendance record and its break logs. |
| `GET` | `/attendance/attendance_calender/?month={month}&year={year}&employee_id={id}` | Authenticated | Monthly attendance, holiday, and weekend calendar with summary data. |

Attendance lists support query filters such as `employee`, `day`, `month`,
`year`, `status`, `check_in`, and `check_out`, plus `page`, `page_size`,
`search`, and `ordering`.

### Payslips and payroll

| Method | Path | Access | Details |
|---|---|---|---|
| `GET` | `/employee/pay_slip/employee_payslips/` | Admin write rule (read endpoint) | Current user's payslip history. |
| `GET` | `/employee/payslip_download/{id}/` | Authenticated | Download or generate the PDF for the requested payslip ID. |
| `POST` | `/employee/pay_slip/get_leaves_data/` | Admin | Body: `employee_id`, `start_date`, `end_date`; previews leave deductions. |
| `POST` | `/employee/pay_slip/get_leaves_data_payslip/` | Admin | Body: `employee_id`, `start_date`, `end_date`; returns attendance/leave calculation data. |
| `POST` | `/employee/pay_slip/generate_manual_payslip/` | Admin | Manual payslip generation. Important fields include `employee_id`, `start_date`, `end_date`, `month`, `year`, `month_name`, salary components, and deductions. |

Normal payslip creation at `/employee/pay_slip/` accepts an `employee` ID,
`start_date`, `end_date`, and salary/deduction components such as
`basic_salary`, `hr_allowance`, `special_allowance`, `tax_deductions`, and
`other_deductions`. The serializer calculates totals and net salary.

### Chat

| Method | Path | Access | Details |
|---|---|---|---|
| `GET` | `/chat/conversations/` | Authenticated | Conversations where the current user participates. |
| `POST` | `/chat/conversations/create/` | Authenticated | Create a conversation. Body includes `type` (`private` or `group`), optional `name`, and `participants` (user ID list). The creator is added as a participant. |
| `DELETE` | `/chat/conversations/{id}/delete/` | Authenticated participant | Delete a conversation the current user participates in. |
| `GET` | `/chat/remaining_users/` | Authenticated | Active users not already in one of the caller's private conversations. |
| `GET` | `/chat/get_conversation_messages/{conversation}/` | Authenticated | Paginated message history for a conversation. |
| `POST` | `/chat/upload/` | Authenticated participant | Upload a message/file using multipart fields `conversation`, `media`, optional `text`, `msg_type`, `reply_to_id`, and `is_edited`. Max file size is 10 MB. Allowed extensions: JPG/JPEG, PNG, GIF, PDF, DOC/DOCX, TXT. |
| `POST` | `/chat/group_profile_upload/` | Authenticated participant | Multipart fields: `conversation_id`, `profile` image. |
| `POST` | `/chat/message_read/{message_id}/` | Authenticated | Mark the message as read. |
| `POST` | `/chat/messages/{message_id}/reactions/` | Authenticated conversation participant | Body: `emoji`. |
| `DELETE` | `/chat/messages/{message_id}/reactions/` | Authenticated | Body: `emoji`; remove the caller's reaction. |
| `POST` | `/chat/keys/set_public_key/` | Authenticated | Body: `public_key`; stores the caller's public encryption key. |
| `GET` | `/chat/keys/get_public_key/?user_id={id}` | Authenticated | Fetch a user's public key; `user_id` is optional and defaults to the caller. |
| `GET` | `/chat/keys/my_keys/` | Authenticated | Return the caller's public-key/encryption status. |

Message REST objects support text or media, optional reply IDs, message type,
reactions, and read information. Encrypted chat fields include
`encrypted_text`, `is_encrypted`, and `nonce`.

### Notifications

| Method | Path | Access | Details |
|---|---|---|---|
| `GET` | `/notify/notifications/unread_count/` | Authenticated | Return the caller's unread notification count. |
| `POST` | `/notify/notifications/mark_all_read/` | Authenticated | Mark all of the caller's unread notifications as read. |
| `POST` | `/notify/notifications/{id}/read/` | Authenticated recipient | Mark one notification as read. |
| `POST` | `/notify/save-fcm-token/` | Authenticated | Body: `token` (or `fcm_token`) and optional `device_name`. |
| `POST` | `/notify/delete-fcm-token/` | Authenticated | Body: `token` (or `fcm_token`); deactivate the caller's matching device token. |

The notifications collection is filtered to unread notifications addressed to
the caller, even though its viewset uses the `IsAdmin` permission class.

### AI assistant and analytics

| Method | Path | Access | Details |
|---|---|---|---|
| `GET`, `POST` | `/ai/conversations/` | Authenticated | List the caller's conversations or create one. |
| `GET`, `PUT`, `PATCH`, `DELETE` | `/ai/conversations/{id}/` | Authenticated owner | Retrieve, update, or delete a conversation belonging to the caller. |
| `GET` | `/ai/conversations/{id}/messages/` | Authenticated owner | Return messages in chronological order. |
| `POST` | `/ai/conversations/{id}/send_message/` | Authenticated owner | Body: `message`. Sends to the assistant and returns `ai_response`, `message_id`, and `intent`. |
| `POST` | `/ai/conversations/quick_query/` | Authenticated | Body: `message`; asks a question and returns a `conversation_id`. The service also stores the user and AI messages in a conversation. |
| `GET` | `/ai/conversations/available_tools/` | Authenticated | List tools available for the caller's role. |
| `POST` | `/ai/conversations/execute_tool/` | Authenticated | Body: `tool_name` and optional `parameters` object. |
| `GET` | `/ai/analytics/` | Authenticated | List query logs; admins/HR see all logs, other roles see their own. |
| `GET` | `/ai/analytics/{id}/` | Authenticated | Retrieve a query log. |
| `GET` | `/ai/analytics/stats/` | Authenticated | Query totals, popular intents, and average processing time. |
| `POST` | `/ai/analytics/rate_response/` | Authenticated owner | Body: `query_id` and `rating` from 1 to 5. |

### Client, project, report, ticket, expense, and inventory endpoints

The collection paths listed in section 3 provide standard CRUD routes for
clients, projects, daily reports, tickets, expense claims, and inventory. The
principal fields visible in the models include:

- Client: `name`, `email`, `company_name`, `phone`, `website`, `country`
- Project: `client`, `title`, `description`, `manager`, `team_members`,
  `start_date`, `status`
- Daily report: `employee`, optional `project`, `report_date`, `title`,
  `description`, `duration`, `status`
- Ticket: `employee`, `title`, `description`, `status`, `priority`
- Expense claim: `employee`, `date`, `amount`, `title`, `description`,
  `claim_status`, optional file, `clearance_status`
- Inventory item: `name`, `quantity`, `description`, `purchased_at`,
  `purchased_by`
- Inventory detail: `item`, `serial_number`, `purchase_date`, `status`,
  `condition`
- Assignment: `inventory_item`, `employee`, `assigned_date`,
  `expected_return_date`, `actual_return_date`, `is_active`
- History: `inventory_item`, optional `employee`, `action`, `notes`

Additional inventory route:

| Method | Path | Access | Details |
|---|---|---|---|
| `GET` | `/employee/item/get_items_for_inventory/` | Authenticated | Return all inventory catalogue items. |

### Company configuration and lookup routes

The standard CRUD patterns apply to department, position, holiday,
announcement, leave type, notification type, and company/client/project
records. The following actions have additional behavior:

| Method | Path | Access | Details |
|---|---|---|---|
| `GET` | `/superadmin/common_data/partial/` | Admin write rule (read endpoint) | Return a small company settings object. |
| `PATCH` | `/superadmin/common_data/update/` | Admin | Partially update company settings and optional policy/handbook files. |
| `DELETE` | `/superadmin/common_data/delete/` | Admin | Delete the singleton company settings record and its policy/handbook files. |
| `PATCH` | `/superadmin/setting_data/update/` | Admin | Partially update the singleton settings record. |
| `DELETE` | `/superadmin/setting_data/delete/` | Admin | Delete the singleton settings record. |
| `GET` | `/superadmin/leave_type/weekend_holiday_list/` | Admin write rule (read endpoint) | Return upcoming holidays and weekends for the current month. |
| `GET` | `/superadmin/profile/all_active_users/` | Authenticated | Return all active users. |

The holiday collection accepts a `year` filter (defaults to the current year).

### Device endpoints

| Method | Path | Access | Details |
|---|---|---|---|
| `POST` | `/superadmin/device/register/` | Authenticated | Body: optional `device_name`. Returns a device tracking token. |
| `GET` | `/superadmin/device/config/?tracking_token={token}` | Tracking token | Return the device's active configuration. |
| `POST` | `/superadmin/activity-log/` | Tracking token | Body requires `tracking_token`. Current implementation validates the token; activity persistence code is commented out. |

## 5. Health and API documentation routes

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/health/` | Checks database, Redis, and cache; returns 200 when healthy and 503 when unhealthy. |
| `GET` | `/ready/` | Simple readiness response. |
| `GET` | `/alive/` | Simple liveness response. |
| `GET` | `/api/schema/` | OpenAPI schema document. |
| `GET` | `/api/schema/swagger-ui/` | Interactive Swagger UI. |
| `GET` | `/api/schema/redoc/` | ReDoc API browser. |
| Django admin | `/admin/` | Django's built-in administration site. |

OpenAPI schema generation currently emits warnings/errors for some API views
that do not declare serializers. Treat the runtime URL configuration and this
source-checked catalogue as authoritative for routes not shown in the schema
UI.

## 6. WebSocket endpoints

WebSockets are connected to the same backend origin as HTTP. A browser normally
uses `ws://` for local HTTP development and `wss://` behind HTTPS. The frontend
supplies the access token as a query parameter:

```text
?token=<access-token>
```

| WebSocket path | Authentication | Purpose |
|---|---|---|
| `/ws/chat/` | JWT token | Global chat events / notifications about conversations |
| `/ws/chat/{conversation_id}/` | JWT token and conversation participation | Live messages for a specific conversation |
| `/ws/notifications/` | JWT token | Push notification updates for the connected user |
| `/ws/ai-chat/` | JWT token | AI assistant conversation |

Chat WebSocket client message types include `send_message`,
`update_message`, `delete_message`, `typing_start`, `typing_stop`,
`tab_visible`, `add_reaction`, `remove_reaction`, `get_messages`, `add_user`,
`remove_user`, and `heartbeat`. Message payloads use related identifiers such
as `conversation_id`, `message_id`, and `text`; encrypted messages can also
include `encrypted_text`, `nonce`, and `is_encrypted`.

AI WebSocket client message types include:

- `user_message` with `message` and optional `conversation_id`
- `user_typing` with an optional `message`
- `response_feedback` with `feedback` and `ai_message_id`
- `get_conversation_list`
- `get_message_details` with `conversation_id`
- `delete_conversation` with `conversation_id`

Notification WebSockets are server-push: the server sends notification event
objects to the connected account. They do not use the HTTP notification
endpoint paths.

## 7. Important implementation and permission notes

These notes describe the current code, not recommended access policy:

1. **Admin account routes:** `AdminRegister` does not declare a permission
   class, and the global REST default is `AllowAny`. Its list, create, detail,
   and inherited CRUD routes should not be assumed to require an admin token.
2. **Custom script route:** `/superadmin/custom_script/` also has no explicit
   permission class. Treat it as publicly reachable unless the deployment
   adds another protection layer.
3. **Profile and leave application viewsets:** They require authentication,
   but their querysets are not consistently restricted to the signed-in user's
   own record. A protected frontend route does not enforce API-level
   ownership.
4. **Read access under `IsAdmin`:** The project's `IsAdmin` permission permits
   all authenticated users to make safe/read requests, while limiting writes
   to role `admin`. Do not read the name as "administrator-only for every
   method."
5. **Leave endpoint variants:** `/superadmin/leave/` sets the employee from
   the signed-in user on create. `/employee/apply_leave/` has a different
   serializer that exposes an `employee` ID field.
6. **Device activity:** `/superadmin/activity-log/` currently checks the
   tracking token, but the code that persists activity records is commented
   out.
7. **API response formats differ:** Some routes return raw serializer data,
   others return a standard response wrapper, and others use pagination.
8. **OpenAPI is incomplete for some views:** Schema generation reported
   serializer inference errors for several APIViews. Use the actual routes
   above when a view is missing from Swagger/ReDoc.

If these APIs are exposed beyond a trusted local development environment,
review and tighten the access-control cases above before deployment.
