# HRMS Idle Detection System Setup

## Overview
This system monitors keyboard/mouse activity and automatically pauses work when an employee is idle for 10+ minutes.

## Architecture
```
Desktop App (.exe) → HTTP API → Django Backend → Auto-pause Work
```

## Setup Steps

### 1. Build Desktop Application

```bash
cd d:\HRMS\idle_monitor
pip install -r requirements.txt
build.bat
```

This creates `HRMS_IdleDetector.exe` in the `dist/` folder.

### 2. Configure Desktop App

Edit `config.json`:
```json
{
  "api_url": "http://localhost:8000",
  "employee_token": "YOUR_JWT_TOKEN_HERE",
  "idle_threshold": 600,
  "employee_id": "YOUR_EMPLOYEE_ID"
}
```

### 3. Get Employee JWT Token

**Method 1: Login API**
```bash
curl -X POST http://localhost:8000/superadmin/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "employee@company.com", "password": "password"}'
```

**Method 2: Django Admin**
- Login to admin panel
- Go to Token section
- Generate token for employee

### 4. Deploy Desktop App

1. Copy `HRMS_IdleDetector.exe` and `config.json` to employee machines
2. Configure `config.json` with each employee's token
3. Run the exe file (runs in background)

## API Endpoints

### Idle Status Endpoint
```
POST /attendance/idle-status/
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "is_idle": true,
  "timestamp": "2024-01-15T10:30:00Z",
  "idle_duration": 605.5
}
```

### Response
```json
{
  "success": true,
  "message": "Work auto-paused due to inactivity",
  "data": {
    "action": "paused",
    "idle_duration": 605.5
  }
}
```

## How It Works

1. **Desktop App**: Monitors keyboard/mouse using Windows API
2. **Idle Detection**: Tracks time since last input
3. **API Call**: Sends idle status to Django backend every 10 minutes
4. **Auto-pause**: Django automatically pauses work if idle
5. **Auto-resume**: Resumes work when activity detected

## Features

- ✅ Real-time idle detection
- ✅ Automatic work pause/resume
- ✅ JWT authentication
- ✅ Configurable idle threshold
- ✅ Windows system integration
- ✅ Background operation

## Troubleshooting

### Common Issues

1. **Token expired**: Refresh JWT token in config.json
2. **API connection failed**: Check network and API URL
3. **Permission denied**: Run as administrator if needed

### Logs
Desktop app shows real-time status in console:
```
🔍 Starting idle detection...
⏱️  Idle threshold: 600 seconds
📊 Status: ACTIVE | Idle time: 45.2s
😴 User is IDLE (inactive for 610.1s)
✓ Idle status sent: IDLE
```

## Security Notes

- JWT tokens should be kept secure
- Desktop app runs locally only
- No sensitive data transmitted except authentication
- HTTPS recommended for production
