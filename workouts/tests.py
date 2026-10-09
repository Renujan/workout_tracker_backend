"""
Basic API tests for the workouts app.
Run: python manage.py test workouts
"""

from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status

from workouts.models import WorkoutPlan, CompletedWorkout


class WorkoutAPITestCase(TestCase):
    """Test workout plans and completed workout history endpoints."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='lifter', password='gym12345')
        self.client.force_authenticate(user=self.user)

    # ── Workout Plans ─────────────────────────────────────────────────────────
    def test_create_workout_plan(self):
        payload = {'name': 'Push Day A', 'category': 'Push', 'estimated_minutes': 60}
        res = self.client.post('/api/v1/workouts/plans/', payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['name'], 'Push Day A')

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

    def test_history_returns_only_own_workouts(self):
        other = User.objects.create_user(username='other2', password='pass')
        CompletedWorkout.objects.create(
            user=other, name='Hidden', date='2026-10-01',
            duration_minutes=40, total_volume_kg=2000, total_sets=10,
        )
        res = self.client.get('/api/v1/workouts/history/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['count'], 0)
