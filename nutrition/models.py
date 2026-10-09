from django.db import models
from django.contrib.auth.models import User


class MealItem(models.Model):
    MEAL_CATEGORY_CHOICES = [
        ('Breakfast', 'Breakfast'), ('Lunch', 'Lunch'),
        ('Snack', 'Snack'), ('Dinner', 'Dinner'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='meal_items')
    date = models.DateField()
    category = models.CharField(max_length=20, choices=MEAL_CATEGORY_CHOICES)
    name = models.CharField(max_length=120)
    calories = models.PositiveIntegerField(default=0)
    protein_grams = models.FloatField(default=0)
    carbs_grams = models.FloatField(default=0)
    fat_grams = models.FloatField(default=0)
    serving_size = models.CharField(max_length=60, blank=True)
    image_url = models.URLField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', 'category']

    def __str__(self):
        return f'{self.user.username} — {self.name} ({self.date})'


class DailyNutrition(models.Model):
    """Aggregated daily nutrition snapshot + targets for a user."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='daily_nutrition')
    date = models.DateField()

    # Actuals
    calories = models.PositiveIntegerField(default=0)
    protein_grams = models.FloatField(default=0)
    carbs_grams = models.FloatField(default=0)
    fat_grams = models.FloatField(default=0)
    water_liters = models.FloatField(default=0)

    # Targets
    target_calories = models.PositiveIntegerField(default=2000)
    target_protein_grams = models.FloatField(default=150)
    target_carbs_grams = models.FloatField(default=250)
    target_fat_grams = models.FloatField(default=65)
    target_water_liters = models.FloatField(default=3.0)

    class Meta:
        ordering = ['-date']
        unique_together = ['user', 'date']

    def __str__(self):
        return f'{self.user.username} — Nutrition {self.date}'
