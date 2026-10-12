"""
API tests for the progress app.
Run: python manage.py test progress
"""

from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
import datetime

from users.models import UserProfile
from progress.models import BodyMeasurement, FitnessGoal, Achievement


class ProgressAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='progress_user', password='password123')
        self.client.force_authenticate(user=self.user)
        self.profile, _ = UserProfile.objects.get_or_create(
            user=self.user,
            defaults={'current_weight_kg': 78.0, 'target_weight_kg': 75.0, 'total_workouts': 10}
        )
        self.today = datetime.date.today()

    def test_create_body_measurement(self):
        payload = {
            'date': self.today.isoformat(),
            'weight_kg': 78.5,
            'body_fat_percent': 16.5,
            'waist_cm': 82.0,
        }
        res = self.client.post('/api/v1/progress/measurements/', payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['weight_kg'], 78.5)

    def test_body_composition_trends(self):
        # Create 2 measurement records
        BodyMeasurement.objects.create(
            user=self.user,
            date=self.today - datetime.timedelta(days=14),
            weight_kg=80.0,
            body_fat_percent=18.0
        )
        BodyMeasurement.objects.create(
            user=self.user,
            date=self.today,
            weight_kg=78.0,
            body_fat_percent=16.5
        )
        res = self.client.get('/api/v1/progress/analytics/trends/?height_cm=180')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(res.data['has_data'])
        self.assertEqual(res.data['total_weight_delta_kg'], -2.0)
        self.assertEqual(res.data['body_fat_delta_percent'], -1.5)
        self.assertIn('current_bmi', res.data)
        self.assertEqual(res.data['bmi_category'], 'Normal')

    def test_evaluate_fitness_goals_action(self):
        goal = FitnessGoal.objects.create(
            user=self.user,
            title='Reach 10 workouts',
            category='workout',
            target_value=10.0,
            current_value=5.0,
            unit='workouts',
            is_completed=False
        )
        res = self.client.post('/api/v1/progress/goals/evaluate/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        goal.refresh_from_db()
        self.assertTrue(goal.is_completed)
        self.assertEqual(goal.current_value, 10.0)
