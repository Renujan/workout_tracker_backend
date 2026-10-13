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
| POST | `/api/v1/auth/password/change/` | Change password with validation |
| GET/PUT | `/api/v1/users/profile/` | Own user profile |
| GET/POST | `/api/v1/users/preferences/` | User unit preferences and weekly target configuration |
| GET | `/api/v1/exercises/` | Exercise library (filter/search) |
| GET | `/api/v1/exercises/categories/` | Exercise filter options matrix |
| GET | `/api/v1/exercises/muscle_groups/` | Muscle groups count distribution |
| GET | `/api/v1/exercises/filter_matrix/` | Filter matrix across muscle, equipment, difficulty |
| GET | `/api/v1/exercises/suggestions/` | Autocomplete exercise search suggestions |
| GET | `/api/v1/exercises/{id}/` | Exercise detail + history |
| GET | `/api/v1/exercises/{id}/pr/` | All-time personal bests for exercise |
| GET/POST | `/api/v1/exercises/records/` | Personal records |
| GET | `/api/v1/exercises/records/overview/` | Personal records summary overview |
| GET/POST | `/api/v1/exercises/history/` | Exercise history points |
| GET/POST | `/api/v1/workouts/plans/` | Workout plans (nested writable exercises) |
| POST | `/api/v1/workouts/plans/{id}/duplicate/` | Clone workout plan template and exercises |
| GET/POST | `/api/v1/workouts/sessions/` | Workout sessions (auto-populates from plan) |
| GET | `/api/v1/workouts/sessions/active/` | Get current active workout session |
| POST | `/api/v1/workouts/sessions/{id}/complete/` | Complete workout (auto volume, PRs, streak, achievements) |
| POST | `/api/v1/workouts/sessions/{id}/add-exercise/` | Dynamically add exercise to active session |
| GET/PATCH | `/api/v1/workouts/sets/{id}/` | Real-time set updates (weight, reps, RPE, completed) |
| GET/POST | `/api/v1/workouts/history/` | Completed workouts history (with exercise breakdown) |
| GET | `/api/v1/workouts/history/export/` | Export workout history to CSV or JSON |
| POST | `/api/v1/workouts/calculator/1rm/` | 1RM calculator (Epley, Brzycki, Lander) |
| POST | `/api/v1/workouts/calculator/calories/` | Estimate calories burned via MET algorithm |
| GET | `/api/v1/workouts/calculator/rest-timer/` | Recommended rest timer based on rep ranges & compound movements |
| GET | `/api/v1/workouts/analytics/weekly-summary/` | Weekly workouts volume and consistency summary |
| GET | `/api/v1/workouts/analytics/activity-calendar/` | Day-by-day activity heatmap and consistency rate |
| GET | `/api/v1/workouts/analytics/volume-progression/` | Week-over-week tonnage volume and progressive overload trends |
| GET/POST | `/api/v1/nutrition/daily/` | Daily nutrition log |
| GET/POST | `/api/v1/nutrition/meals/` | Meal items |
| POST | `/api/v1/nutrition/recommendations/` | BMR, TDEE & macro targets calculator |
| GET | `/api/v1/nutrition/summary/daily/` | Daily consumed vs target macro summary |
| GET/POST | `/api/v1/nutrition/hydration/` | Water intake tracking and dynamic hydration targets |
| GET/POST | `/api/v1/nutrition/recommendations/timing/` | Pre, intra, and post workout nutrient timing guidelines |
| GET/POST | `/api/v1/progress/measurements/` | Body measurements |
| GET | `/api/v1/progress/analytics/trends/` | Body composition trend analysis and BMI |
| GET | `/api/v1/progress/analytics/circumference/` | Body circumference measurement delta and symmetry tracker |
| GET/POST | `/api/v1/progress/photos/` | Progress photos |
| GET/POST | `/api/v1/progress/goals/` | Fitness goals |
| POST | `/api/v1/progress/goals/evaluate/` | Auto-evaluate active fitness goals |
| GET/POST | `/api/v1/progress/achievements/` | Achievements |
| POST | `/api/v1/progress/achievements/sync/` | Evaluate milestones and unlock achievement badges |
| GET | `/api/v1/progress/insights/` | Fitness insights |
| GET | `/api/v1/health/` | Health check with database latency ping and X-Process-Time-Ms |
| GET | `/api/v1/export/userdata/` | Unified user data archive export for portability |

---

## 🧪 Running Tests

```bash
python manage.py test
# Ran 39 tests — OK (100% pass)
```

---

## 🔗 Related Repository

**Frontend**: [workout_tracker_frontend](https://github.com/Renujan/workout_tracker_frontend) — React + TypeScript + Vite

