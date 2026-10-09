# ProgressX — Workout Tracker Backend

Django REST Framework backend for the ProgressX fitness tracking application.

---

## 🏗️ Project Architecture

```
workout_tracker_backend/
├── core/                         # Django project config
│   ├── settings.py               # Dev settings (DRF, JWT, CORS, all apps)
│   ├── settings_prod.py          # Production overrides (env vars, PostgreSQL)
│   ├── urls.py                   # Root URL conf (/api/v1/)
│   ├── views.py                  # Health-check endpoint
│   └── management/commands/
│       └── create_admin.py       # Auto-create superuser command
│
├── users/                        # Auth + user profiles
├── exercises/                    # Exercise library + history + PRs
│   └── management/commands/
│       └── seed_data.py          # Full demo data seeder
├── workouts/                     # Workout plans, sessions, sets, history
├── nutrition/                    # Daily macros + meal logging
├── progress/                     # Body measurements, goals, achievements, insights
│
├── requirements.txt
├── .env.example
└── manage.py
```

---

## 🚀 Tech Stack

| Layer | Technology |
|---|---|
| Framework | Django 5.2 |
| API | Django REST Framework 3.16 |
| Auth | JWT via `djangorestframework-simplejwt` |
| CORS | `django-cors-headers` |
| Filtering | `django-filter` |
| Database | SQLite (dev) → PostgreSQL (prod via DATABASE_URL) |
| Image upload | Pillow |

---

## 📅 Development Log

### Day 1 — 2026-10-09
- ✅ Initialized Django project (`core/`) with DRF, JWT, CORS, django-filter
- ✅ Built 5 Django apps: `users`, `workouts`, `exercises`, `nutrition`, `progress`
- ✅ 14 models, 13 serializers, 11 API ViewSets
- ✅ Production settings split (`settings_prod.py`) with env var support
- ✅ Seed command: `python manage.py seed_data` (demo user + full dataset)
- ✅ Health check: `GET /api/v1/health/`
- ✅ 21 API tests — all passing
- ✅ `python manage.py check` — 0 issues
- ✅ 13 git commits pushed to GitHub

### Coming Up (Day 2+)
- 🔜 Wire React service layer to live DRF endpoints (replace mock data)
- 🔜 JWT axios interceptors in frontend
- 🔜 PostgreSQL + Railway/Render deployment
- 🔜 Django Channels for real-time rest timer WebSocket

---

## ⚙️ Getting Started

```bash
# 1. Clone
git clone https://github.com/Renujan/workout_tracker_backend.git
cd workout_tracker_backend

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run migrations
python manage.py migrate

# 5. Seed demo data
python manage.py seed_data
# Creates: renujan / gym12345

# 6. (Optional) Create admin superuser
python manage.py create_admin
# Creates: admin / admin1234

# 7. Start development server
python manage.py runserver
# API: http://localhost:8000/api/v1/
# Admin: http://localhost:8000/admin/
```

---

## 🔌 API Endpoints (v1)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/health/` | Health check (no auth) |
| POST | `/api/v1/auth/register/` | Register → JWT pair |
| POST | `/api/v1/auth/login/` | Login → JWT pair |
| POST | `/api/v1/auth/logout/` | Blacklist refresh token |
| POST | `/api/v1/auth/token/refresh/` | Refresh access token |
| GET/PUT | `/api/v1/users/profile/` | Own user profile |
| GET | `/api/v1/exercises/` | Exercise library (filter/search) |
| GET | `/api/v1/exercises/{id}/` | Exercise detail + history |
| GET/POST | `/api/v1/exercises/records/` | Personal records |
| GET/POST | `/api/v1/exercises/history/` | Exercise history points |
| GET/POST | `/api/v1/workouts/plans/` | Workout plans |
| GET/POST | `/api/v1/workouts/sessions/` | Active sessions |
| GET/POST | `/api/v1/workouts/history/` | Completed workouts |
| GET/POST | `/api/v1/nutrition/daily/` | Daily nutrition log |
| GET/POST | `/api/v1/nutrition/meals/` | Meal items |
| GET/POST | `/api/v1/progress/measurements/` | Body measurements |
| GET/POST | `/api/v1/progress/photos/` | Progress photos |
| GET/POST | `/api/v1/progress/goals/` | Fitness goals |
| GET/POST | `/api/v1/progress/achievements/` | Achievements |
| GET | `/api/v1/progress/insights/` | Fitness insights |

---

## 🧪 Running Tests

```bash
python manage.py test users exercises workouts nutrition
# Ran 21 tests — OK
```

---

## 🔗 Related Repository

**Frontend**: [workout_tracker_frontend](https://github.com/Renujan/workout_tracker_frontend) — React + TypeScript + Vite
