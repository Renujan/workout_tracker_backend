from django.db import models
from django.contrib.auth.models import User


class Exercise(models.Model):
    MUSCLE_GROUP_CHOICES = [
        ('Chest', 'Chest'), ('Back', 'Back'), ('Shoulders', 'Shoulders'),
        ('Biceps', 'Biceps'), ('Triceps', 'Triceps'), ('Legs', 'Legs'),
        ('Abs', 'Abs'), ('Cardio', 'Cardio'),
    ]
    EQUIPMENT_CHOICES = [
        ('Barbell', 'Barbell'), ('Dumbbell', 'Dumbbell'), ('Machine', 'Machine'),
        ('Cable', 'Cable'), ('Bodyweight', 'Bodyweight'),
    ]
    DIFFICULTY_CHOICES = [
        ('Beginner', 'Beginner'), ('Intermediate', 'Intermediate'), ('Advanced', 'Advanced'),
    ]

    name = models.CharField(max_length=120, unique=True)
    muscle_group = models.CharField(max_length=20, choices=MUSCLE_GROUP_CHOICES)
    equipment = models.CharField(max_length=20, choices=EQUIPMENT_CHOICES)
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES)
    description = models.TextField(blank=True)
    image_url = models.URLField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Exercise'
        verbose_name_plural = 'Exercises'

    def __str__(self):
        return f'{self.name} ({self.muscle_group})'


class ExerciseHistory(models.Model):
    """Per-user, per-date performance data for one exercise."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='exercise_history')
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE, related_name='history')
    date = models.DateField()
    weight_kg = models.FloatField()
    reps = models.PositiveIntegerField()
    volume_kg = models.FloatField(help_text='weight_kg * reps')
    estimated_1rm = models.FloatField(help_text='Epley formula: w*(1 + r/30)')

    class Meta:
        ordering = ['-date']
        unique_together = ['user', 'exercise', 'date']

    def save(self, *args, **kwargs):
        self.volume_kg = self.weight_kg * self.reps
        self.estimated_1rm = self.weight_kg * (1 + self.reps / 30)
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.user.username} — {self.exercise.name} on {self.date}'


class PersonalRecord(models.Model):
    CATEGORY_CHOICES = [
        ('strength', 'Strength'), ('rep', 'Rep'), ('volume', 'Volume'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='personal_records')
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE, related_name='personal_records')
    weight_kg = models.FloatField()
    reps = models.PositiveIntegerField()
    previous_weight_kg = models.FloatField(default=0)
    previous_reps = models.PositiveIntegerField(default=0)
    improvement_kg = models.FloatField(default=0)
    date = models.DateField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='strength')

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f'{self.user.username} PR — {self.exercise.name} {self.weight_kg}kg x {self.reps}'
