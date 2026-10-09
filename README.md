# ProgressX — Workout Tracker Backend

Django REST Framework backend for the ProgressX fitness tracking application.

---

## 🏗️ Project Architecture

```
workout_tracker_backend/
├── core/               # Django project config (settings, urls, wsgi, asgi)
├── users/              # User profiles, authentication (JWT)
├── workouts/           # Workout plans, sessions, sets
├── exercises/          # Exercise library, personal records
├── nutrition/          # Macro tracking, meal logs
├── progress/           # Body measurements, progress photos, insights
├── requirements.txt
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
| Database | SQLite (dev) → PostgreSQL (prod) |
| Image upload | Pillow |

---

## 📅 Development Log

### Day 1 — 2026-10-09 (Today)
- ✅ Initialized Django project (`core/`)
- ✅ Created 5 apps: `users`, `workouts`, `exercises`, `nutrition`, `progress`
- ✅ Configured CORS, JWT, DRF settings
- ✅ Built `users` app: `UserProfile` model, registration, login, JWT auth endpoints
- ✅ Built `exercises` app: `Exercise`, `PersonalRecord` models + serializers + ViewSets
- ✅ Built `workouts` app: `WorkoutPlan`, `WorkoutSession`, `WorkoutSet`, `CompletedWorkout` models
- ✅ Built `nutrition` app: `DailyNutrition`, `MealItem` models + serializers
- ✅ Built `progress` app: `BodyMeasurement`, `ProgressPhoto`, `FitnessGoal`, `Achievement`, `FitnessInsight` models
- ✅ Wired all app URLs into `core/urls.py` under `/api/v1/`
- ✅ Added seed management command (`python manage.py seed_data`)
- ✅ Full README documentation

### Coming Up (Day 2+)
- 🔜 Wire frontend service layer to live DRF endpoints
- 🔜 Implement filtering, search, and pagination
- 🔜 Add PostgreSQL support + environment config
- 🔜 Deploy to Railway / Render

---

## ⚙️ Getting Started

```bash
# 1. Clone
git clone https://github.com/Renujan/workout_tracker_backend.git
cd workout_tracker_backend

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate   # Windows
# source venv/bin/activate  # macOS/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run migrations
python manage.py migrate

# 5. Seed demo data (optional)
python manage.py seed_data

# 6. Start development server
python manage.py runserver
```

---

## 🔌 API Endpoints (v1)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register/` | Register new user |
| POST | `/api/v1/auth/login/` | Login → JWT tokens |
| POST | `/api/v1/auth/token/refresh/` | Refresh access token |
| GET/PUT | `/api/v1/users/profile/` | Get / update user profile |
| GET | `/api/v1/exercises/` | List all exercises |
| GET | `/api/v1/exercises/{id}/` | Exercise detail |
| GET/POST | `/api/v1/exercises/records/` | Personal records |
| GET/POST | `/api/v1/workouts/plans/` | Workout plans |
| GET/POST | `/api/v1/workouts/sessions/` | Workout sessions |
| GET/POST | `/api/v1/workouts/history/` | Completed workouts |
| GET/POST | `/api/v1/nutrition/daily/` | Daily nutrition log |
| GET/POST | `/api/v1/nutrition/meals/` | Meal items |
| GET/POST | `/api/v1/progress/measurements/` | Body measurements |
| GET/POST | `/api/v1/progress/goals/` | Fitness goals |
| GET/POST | `/api/v1/progress/achievements/` | Achievements |
| GET | `/api/v1/progress/insights/` | Fitness insights |

---

## 🔗 Related Repository

**Frontend**: [workout_tracker_frontend](https://github.com/Renujan/workout_tracker_frontend) — React + TypeScript + Vite
