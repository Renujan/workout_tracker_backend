"""
Comprehensive API tests for the workouts app:
- Workout plans with nested exercises
- Active workout sessions and auto-population from plans
- Set-level updates during workouts
- Dynamic exercise additions to active sessions
- Workout completion automation:
  * CompletedWorkout persistence
  * UserProfile totals, volume, and streak updates
  * PR detection and history recording
  * Achievement unlocking

Run: python manage.py test workouts
"""

from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status

from exercises.models import Exercise, PersonalRecord, ExerciseHistory
from users.models import UserProfile
from progress.models import Achievement
from workouts.models import (
    WorkoutPlan, PlanExercise, WorkoutSession,
    SessionExercise, WorkoutSet, CompletedWorkout
)


class WorkoutAPITestCase(TestCase):
    """Test workout plans and completed workout history endpoints."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='lifter', password='gym12345')
        self.client.force_authenticate(user=self.user)
        self.profile, _ = UserProfile.objects.get_or_create(user=self.user)

        self.bench = Exercise.objects.create(
            name='Bench Press',
            muscle_group='Chest',
            equipment='Barbell',
            difficulty='Intermediate'
        )
        self.squat = Exercise.objects.create(
            name='Barbell Squat',
            muscle_group='Legs',
            equipment='Barbell',
            difficulty='Intermediate'
        )

    # ── Workout Plans ─────────────────────────────────────────────────────────
    def test_create_workout_plan(self):
        payload = {'name': 'Push Day A', 'category': 'Push', 'estimated_minutes': 60}
        res = self.client.post('/api/v1/workouts/plans/', payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['name'], 'Push Day A')

    def test_create_workout_plan_with_nested_exercises(self):
        payload = {
            'name': 'Chest & Legs',
            'category': 'Full Body',
            'estimated_minutes': 75,
            'exercises': [
                {
                    'exercise': self.bench.id,
                    'order': 0,
                    'target_sets': 4,
                    'target_reps': '6-8',
                    'target_weight_kg': 85.0
                },
                {
                    'exercise': self.squat.id,
                    'order': 1,
                    'target_sets': 3,
                    'target_reps': '5',
                    'target_weight_kg': 120.0
                }
            ]
        }
        res = self.client.post('/api/v1/workouts/plans/', payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(res.data['exercises']), 2)
        self.assertEqual(res.data['exercise_count'], 2)
        self.assertEqual(res.data['estimated_sets'], 7)

        plan = WorkoutPlan.objects.get(id=res.data['id'])
        self.assertEqual(plan.exercises.count(), 2)

    def test_workout_plans_scoped_to_user(self):
        other = User.objects.create_user(username='other', password='pass')
        WorkoutPlan.objects.create(user=other, name='Other Plan', category='Pull')
        res = self.client.get('/api/v1/workouts/plans/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['count'], 0)

    def test_filter_plans_by_category(self):
        WorkoutPlan.objects.create(user=self.user, name='Legs Day', category='Legs')
        WorkoutPlan.objects.create(user=self.user, name='Push Day', category='Push')
        res = self.client.get('/api/v1/workouts/plans/?category=Legs')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['count'], 1)
        self.assertEqual(res.data['results'][0]['name'], 'Legs Day')

    # ── Sessions & Auto-Population ────────────────────────────────────────────
    def test_create_session_auto_populates_from_plan(self):
        plan = WorkoutPlan.objects.create(user=self.user, name='Push Plan', category='Push')
        PlanExercise.objects.create(
            plan=plan, exercise=self.bench, order=0,
            target_sets=3, target_reps='8-10', target_weight_kg=80.0
        )

        res = self.client.post('/api/v1/workouts/sessions/', {
            'plan': plan.id,
            'name': 'Today Push Session',
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        session_id = res.data['id']

        session = WorkoutSession.objects.get(id=session_id)
        self.assertEqual(session.exercises.count(), 1)
        se = session.exercises.first()
        self.assertEqual(se.sets.count(), 3)
        first_set = se.sets.first()
        self.assertEqual(first_set.target_weight_kg, 80.0)
        self.assertEqual(first_set.completed, False)

    # ── Active Session Query ──────────────────────────────────────────────────
    def test_get_active_session(self):
        # When no active session exists
        res = self.client.get('/api/v1/workouts/sessions/active/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIsNone(res.data)

        # Create active session
        session = WorkoutSession.objects.create(user=self.user, name='Active Now')
        res = self.client.get('/api/v1/workouts/sessions/active/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['id'], session.id)

    # ── Set-Level Updates ─────────────────────────────────────────────────────
    def test_set_level_update(self):
        session = WorkoutSession.objects.create(user=self.user, name='Live Session')
        se = SessionExercise.objects.create(session=session, exercise=self.bench, order=0)
        s = WorkoutSet.objects.create(session_exercise=se, set_number=1, weight_kg=70, reps=0)

        patch_res = self.client.patch(f'/api/v1/workouts/sets/{s.id}/', {
            'completed': True,
            'weight_kg': 82.5,
            'reps': 8,
            'rpe': 8.5
        }, format='json')

        self.assertEqual(patch_res.status_code, status.HTTP_200_OK)
        self.assertEqual(patch_res.data['completed'], True)
        self.assertEqual(patch_res.data['weight_kg'], 82.5)
        self.assertEqual(patch_res.data['reps'], 8)
        self.assertEqual(patch_res.data['rpe'], 8.5)

        s.refresh_from_db()
        self.assertTrue(s.completed)
        self.assertEqual(s.weight_kg, 82.5)

    # ── Add Exercise to Session ───────────────────────────────────────────────
    def test_add_exercise_to_active_session(self):
        session = WorkoutSession.objects.create(user=self.user, name='Quick Session')
        res = self.client.post(f'/api/v1/workouts/sessions/{session.id}/add-exercise/', {
            'exercise': self.squat.id,
            'target_sets': 4,
            'target_weight_kg': 100.0,
            'target_reps': '5'
        }, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        session.refresh_from_db()
        self.assertEqual(session.exercises.count(), 1)
        se = session.exercises.first()
        self.assertEqual(se.exercise, self.squat)
        self.assertEqual(se.sets.count(), 4)

    # ── Workout Completion Automation ─────────────────────────────────────────
    def test_complete_workout_automation(self):
        # 1. Setup session with 2 completed sets (one over 100kg to test Century Club PR)
        session = WorkoutSession.objects.create(
            user=self.user, name='Heavy Bench Day', elapsed_seconds=3600
        )
        se = SessionExercise.objects.create(session=session, exercise=self.bench, order=0)
        set1 = WorkoutSet.objects.create(
            session_exercise=se, set_number=1, weight_kg=90, reps=8, completed=True
        )
        set2 = WorkoutSet.objects.create(
            session_exercise=se, set_number=2, weight_kg=102.5, reps=5, completed=True
        )

        # 2. Call complete endpoint
        res = self.client.post(f'/api/v1/workouts/sessions/{session.id}/complete/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        # 3. Verify session completed
        session.refresh_from_db()
        self.assertTrue(session.is_completed)
        self.assertIsNotNone(session.completed_at)

        # 4. Verify CompletedWorkout was created with exercise details
        cw = CompletedWorkout.objects.get(session=session)
        expected_volume = (90 * 8) + (102.5 * 5)  # 720 + 512.5 = 1232.5
        self.assertEqual(cw.total_volume_kg, expected_volume)
        self.assertEqual(cw.total_sets, 2)
        self.assertEqual(cw.duration_minutes, 60)
        self.assertEqual(len(res.data['exercises']), 1)
        self.assertEqual(res.data['exercises'][0]['max_weight_kg'], 102.5)

        # 5. Verify UserProfile stats updated
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.total_workouts, 1)
        self.assertEqual(self.profile.total_volume_kg, expected_volume)
        self.assertEqual(self.profile.total_sets, 2)
        self.assertEqual(self.profile.total_prs, 1)
        self.assertGreaterEqual(self.profile.current_streak, 1)
        self.assertGreaterEqual(self.profile.weekly_workouts_completed, 1)

        # 6. Verify PersonalRecord detected & saved
        prs = PersonalRecord.objects.filter(user=self.user, exercise=self.bench)
        self.assertEqual(prs.count(), 1)
        pr = prs.first()
        self.assertEqual(pr.weight_kg, 102.5)
        self.assertEqual(pr.reps, 5)

        set2.refresh_from_db()
        self.assertTrue(set2.is_pr)

        # 7. Verify ExerciseHistory point created
        eh = ExerciseHistory.objects.filter(user=self.user, exercise=self.bench).first()
        self.assertIsNotNone(eh)
        self.assertEqual(eh.weight_kg, 102.5)

        # 8. Verify Achievements unlocked: "First Workout" & "Century Club"
        ach_first = Achievement.objects.filter(user=self.user, title='First Workout').first()
        self.assertIsNotNone(ach_first)
        self.assertTrue(ach_first.unlocked)

        ach_century = Achievement.objects.filter(user=self.user, title='Century Club').first()
        self.assertIsNotNone(ach_century)
        self.assertTrue(ach_century.unlocked)

    # ── Workout History ───────────────────────────────────────────────────────
    def test_create_completed_workout(self):
        payload = {
            'name': 'Push Day A',
            'category': 'Push',
            'date': '2026-10-09',
            'duration_minutes': 65,
            'total_volume_kg': 4820.0,
            'total_sets': 20,
        }
        res = self.client.post('/api/v1/workouts/history/', payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['total_volume_kg'], 4820.0)

        # Verify profile totals were updated
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.total_workouts, 1)

    def test_history_returns_only_own_workouts(self):
        other = User.objects.create_user(username='other2', password='pass')
        CompletedWorkout.objects.create(
            user=other, name='Hidden', date='2026-10-01',
            duration_minutes=40, total_volume_kg=2000, total_sets=10,
        )
        res = self.client.get('/api/v1/workouts/history/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['count'], 0)

    # ── 1RM Calculator ────────────────────────────────────────────────────────
    def test_one_rep_max_calculator_epley(self):
        payload = {'weight_kg': 100, 'reps': 5, 'formula': 'epley'}
        res = self.client.post('/api/v1/workouts/calculator/1rm/', payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # 100 * (1 + 5/30) = 116.666... -> 116.7
        self.assertAlmostEqual(res.data['estimated_1rm'], 116.7, delta=0.2)
        self.assertIn('percentages', res.data)
        self.assertIn('rep_table', res.data)
        self.assertEqual(res.data['formula'], 'epley')

    # ── Plan Duplicate ────────────────────────────────────────────────────────
    def test_duplicate_workout_plan(self):
        plan = WorkoutPlan.objects.create(
            user=self.user,
            name='Original Push Routine',
            category='Push',
            estimated_minutes=45,
        )
        PlanExercise.objects.create(
            plan=plan,
            exercise=self.bench,
            order=1,
            target_sets=3,
            target_reps='8-12',
            target_weight_kg=80.0
        )
        url = f'/api/v1/workouts/plans/{plan.id}/duplicate/'
        res = self.client.post(url, {'name': 'Custom Cloned Plan'}, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['name'], 'Custom Cloned Plan')
        self.assertNotEqual(res.data['id'], plan.id)
        # Verify exercises were cloned
        self.assertEqual(len(res.data['exercises']), 1)

    # ── Calorie Calculator ────────────────────────────────────────────────────
    def test_calorie_estimate_view(self):
        payload = {
            'duration_minutes': 60,
            'total_volume_kg': 3000.0,
            'category': 'Push'
        }
        res = self.client.post('/api/v1/workouts/calculator/calories/', payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertGreater(res.data['estimated_calories_burned'], 0)
        self.assertEqual(res.data['duration_minutes'], 60)

    # ── Rest Timer Calculator ─────────────────────────────────────────────────
    def test_rest_timer_calculator(self):
        res = self.client.get('/api/v1/workouts/calculator/rest-timer/?reps=5&exercise_type=compound')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['target_reps'], 5)
        self.assertEqual(res.data['exercise_type'], 'compound')
        self.assertEqual(res.data['recommended_rest_seconds'], 210)  # 180 + 30
        self.assertEqual(res.data['training_goal'], 'Strength & Power')

    # ── Activity Calendar ─────────────────────────────────────────────────────
    def test_workout_activity_calendar(self):
        from django.utils import timezone
        today = timezone.now().date()
        CompletedWorkout.objects.create(
            user=self.user, name='Leg Day', date=today,
            duration_minutes=50, total_volume_kg=4000, total_sets=16, category='Legs'
        )
        res = self.client.get('/api/v1/workouts/analytics/activity-calendar/?days=14')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['days_requested'], 14)
        self.assertGreaterEqual(res.data['active_days_count'], 1)
        self.assertEqual(len(res.data['calendar']), 14)
        today_entry = next((d for d in res.data['calendar'] if d['date'] == today.isoformat()), None)
        self.assertIsNotNone(today_entry)
        self.assertTrue(today_entry['active'])
        self.assertEqual(today_entry['volume_kg'], 4000.0)





