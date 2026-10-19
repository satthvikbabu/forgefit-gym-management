# Gym Management & Fitness Analytics System

A Python + Flask REST API for gym member management, memberships, attendance, workout plans, fitness progress, and business analytics. Uses SQLite for storage and Pandas/NumPy/Matplotlib for analysis and visualizations.

## Features

- Member registration, searching, profile updates, and membership status tracking
- Monthly, quarterly, and yearly membership plans
- Membership renewal and recorded payment amounts
- Attendance records
- Trainer-assigned workout plans and progress logs
- Analytics: active/expired members, monthly registrations, attendance, popular workouts, revenue, and upcoming expiries
- Four generated charts
- Input validation, SQLite foreign keys, request logging, and friendly JSON errors
- API endpoint documentation at `/api/docs`

## Requirements

- Python 3.10+
- Postman (for manual API testing)

## Setup (Windows PowerShell)

```powershell
cd python-gym-system
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
.\.venv\Scripts\python.exe app.py
```

If `py` is unavailable, use `python -m venv .venv`. If you have a particular Python executable, use that executable to create the environment.

The API runs at `http://127.0.0.1:5000`. The database is automatically created at `data/gym.db`.

## Quick test

### 1. Health check
`GET http://127.0.0.1:5000/api/health`

### 2. Register a member
`POST http://127.0.0.1:5000/api/members`

Set Postman **Body → raw → JSON** and send:

```json
{
  "name": "Aarav Kumar",
  "age": 22,
  "gender": "male",
  "weight": 72.5,
  "fitness_goal": "Build muscle",
  "plan": "monthly"
}
```

The response includes the new member ID. Use that ID in the next requests.

### 3. Record attendance
`POST http://127.0.0.1:5000/api/attendance`

```json
{
  "member_id": 1,
  "notes": "Evening session"
}
```

### 4. Assign a workout
`POST http://127.0.0.1:5000/api/workouts`

```json
{
  "member_id": 1,
  "exercise_name": "Squat",
  "sets": 3,
  "repetitions": 12,
  "duration_minutes": 15,
  "trainer_notes": "Focus on form",
  "trainer_name": "Coach Priya"
}
```

### 5. Log workout progress
`POST http://127.0.0.1:5000/api/workouts/1/progress`

```json
{
  "completed_sets": 3,
  "completed_repetitions": 12,
  "completed_minutes": 15,
  "notes": "Completed as planned"
}
```

### 6. View analytics
`GET http://127.0.0.1:5000/api/analytics`

### 7. Generate charts
`POST http://127.0.0.1:5000/api/analytics/charts`

Chart PNG files are saved in `analytics/generated/`.

## API reference

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/` | Project information |
| GET | `/api/health` | Health check |
| GET | `/api/docs` | Endpoint reference |
| POST | `/api/members` | Register member |
| GET | `/api/members` | List members; optional `q` and `status` filters |
| GET | `/api/members/<id>` | Get member |
| PUT | `/api/members/<id>` | Update member |
| POST | `/api/members/<id>/renew` | Renew membership |
| POST | `/api/attendance` | Record attendance |
| GET | `/api/attendance` | List attendance; optional `member_id` |
| POST | `/api/workouts` | Assign workout |
| GET | `/api/workouts` | List workouts; optional `member_id` |
| GET | `/api/members/<id>/workouts` | List member's plans |
| POST | `/api/workouts/<id>/progress` | Log workout progress |
| GET | `/api/analytics` | Analytics data |
| POST | `/api/analytics/charts` | Generate charts |

Membership plans are `monthly`, `quarterly`, or `yearly`. Default example prices are ₹1,500, ₹4,000, and ₹14,000; override by passing `amount` during registration or renewal. These are sample defaults, not market-price claims.

## Suggested Postman testing

1. Call the health endpoint.
2. Register a member and note the returned `id`.
3. Fetch the member and update their profile.
4. Record attendance.
5. Assign a workout and log progress using its returned ID.
6. Renew the membership.
7. Fetch analytics and generate charts.
8. Test validation with missing fields, invalid plan names, and unknown IDs.

Include your own Postman screenshots in the `screenshots/postman/` folder for final submission.

## Project structure

```text
python-gym-system/
├── app.py
├── models/
│   └── database.py
├── services/
│   └── gym_service.py
├── analytics/
│   ├── charts.py
│   └── generated/
├── data/                 # SQLite DB generated on first run
├── tests/
├── screenshots/postman/
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## Notes and limitations

- This is an educational internship project, not a production-ready system.
- Authentication/authorization is not included; do not expose it publicly with real member data without adding access controls.
- Payment records are simple records for analytics, not payment-gateway transactions.
- Membership durations use fixed day counts (30/90/365).
- Member and workout data are local to the SQLite database.
- Use synthetic/demo data in public screenshots and demo videos.
