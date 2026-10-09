"""
Basic API tests for the nutrition app.
Run: python manage.py test nutrition
"""

from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
import datetime


class NutritionAPITestCase(TestCase):
    """Test meal logging and daily nutrition endpoints."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='eater', password='gym12345')
        self.client.force_authenticate(user=self.user)
        self.today = str(datetime.date.today())

    def test_log_meal_item(self):
        payload = {
            'date': self.today, 'category': 'Breakfast',
            'name': 'Oats + Protein', 'calories': 520,
            'protein_grams': 42.0, 'carbs_grams': 65.0,
            'fat_grams': 8.0, 'serving_size': '1 bowl',
        }
        res = self.client.post('/api/v1/nutrition/meals/', payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['name'], 'Oats + Protein')

    def test_meals_scoped_to_user(self):
        other = User.objects.create_user(username='other', password='pass')
        from nutrition.models import MealItem
        MealItem.objects.create(
            user=other, date=self.today, category='Lunch',
            name='Hidden Meal', calories=600, protein_grams=40,
            carbs_grams=50, fat_grams=15,
        )
        res = self.client.get('/api/v1/nutrition/meals/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['count'], 0)

    def test_create_daily_nutrition_snapshot(self):
        payload = {
            'date': self.today,
            'calories': 2150, 'target_calories': 2500,
            'protein_grams': 112.0, 'target_protein_grams': 150.0,
            'carbs_grams': 230.0, 'target_carbs_grams': 300.0,
            'fat_grams': 60.0, 'target_fat_grams': 80.0,
            'water_liters': 2.5, 'target_water_liters': 3.0,
        }
        res = self.client.post('/api/v1/nutrition/daily/', payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertFalse(res.data['protein_hit'])  # 112 < 150

    def test_filter_meals_by_category(self):
        from nutrition.models import MealItem
        MealItem.objects.create(
            user=self.user, date=self.today, category='Breakfast',
            name='Eggs', calories=300, protein_grams=28, carbs_grams=2, fat_grams=18,
        )
        MealItem.objects.create(
            user=self.user, date=self.today, category='Dinner',
            name='Chicken', calories=650, protein_grams=55, carbs_grams=40, fat_grams=12,
        )
        res = self.client.get('/api/v1/nutrition/meals/?category=Breakfast')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['count'], 1)
        self.assertEqual(res.data['results'][0]['name'], 'Eggs')
