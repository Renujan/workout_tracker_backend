"""
Basic API tests for the exercises app.
Run: python manage.py test exercises
"""

from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status

from exercises.models import Exercise, PersonalRecord


class ExerciseAPITestCase(TestCase):
    """Test the exercise library and personal records endpoints."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='gymrat', password='gym12345')
        self.client.force_authenticate(user=self.user)

        self.exercise = Exercise.objects.create(
            name='Bench Press',
            muscle_group='Chest',
            equipment='Barbell',
            difficulty='Intermediate',
            description='Classic chest compound.',
        )

    # ── Exercise Library ──────────────────────────────────────────────────────
    def test_list_exercises_returns_200(self):
        res = self.client.get('/api/v1/exercises/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(res.data['results']), 1)

    def test_filter_exercises_by_muscle_group(self):
        res = self.client.get('/api/v1/exercises/?muscle_group=Chest')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        for item in res.data['results']:
            self.assertEqual(item['muscle_group'], 'Chest')

    def test_exercise_detail_returns_correct_name(self):
        res = self.client.get(f'/api/v1/exercises/{self.exercise.pk}/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['name'], 'Bench Press')

    def test_unauthenticated_cannot_list_exercises(self):
        anon = APIClient()
        res = anon.get('/api/v1/exercises/')
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    # ── Personal Records ──────────────────────────────────────────────────────
    def test_create_personal_record(self):
        payload = {
            'exercise': self.exercise.pk,
            'weight_kg': 100.0,
            'reps': 3,
            'previous_weight_kg': 95.0,
            'previous_reps': 4,
            'improvement_kg': 5.0,
            'date': '2026-10-09',
            'category': 'strength',
        }
        res = self.client.post('/api/v1/exercises/records/', payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['weight_kg'], 100.0)

    def test_personal_records_scoped_to_user(self):
        other = User.objects.create_user(username='other', password='pass1234')
        PersonalRecord.objects.create(
            user=other, exercise=self.exercise,
            weight_kg=80, reps=5,
            date='2026-10-01', category='strength',
        )
        res = self.client.get('/api/v1/exercises/records/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # Current user has no PRs yet
        self.assertEqual(res.data['count'], 0)

    # ── Category & Muscle Group Actions ───────────────────────────────────────
    def test_exercise_categories_action(self):
        res = self.client.get('/api/v1/exercises/categories/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('muscle_groups', res.data)
        self.assertIn('equipment', res.data)
        self.assertIn('difficulty', res.data)
        self.assertIn('Chest', res.data['muscle_groups'])

    def test_exercise_muscle_groups_count_action(self):
        res = self.client.get('/api/v1/exercises/muscle_groups/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(any(item['muscle_group'] == 'Chest' for item in res.data))

    def test_exercise_filter_matrix(self):
        res = self.client.get('/api/v1/exercises/filter_matrix/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('total_exercises', res.data)
        self.assertIn('by_muscle_group', res.data)
        self.assertIn('by_equipment', res.data)
        self.assertIn('by_difficulty', res.data)

    def test_exercise_suggestions(self):
        res = self.client.get('/api/v1/exercises/suggestions/?q=Bench')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(len(res.data) >= 1)
        self.assertEqual(res.data[0]['name'], 'Bench Press')

