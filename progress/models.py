from django.db import models
from django.contrib.auth.models import User


class BodyMeasurement(models.Model):
    """User's body composition snapshot on a given date."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='body_measurements')
    date = models.DateField()
    weight_kg = models.FloatField()
    body_fat_percent = models.FloatField(null=True, blank=True)
    chest_cm = models.FloatField(null=True, blank=True)
    arms_cm = models.FloatField(null=True, blank=True)
    waist_cm = models.FloatField(null=True, blank=True)
    thighs_cm = models.FloatField(null=True, blank=True)

    class Meta:
        ordering = ['-date']
        unique_together = ['user', 'date']

    def __str__(self):
        return f'{self.user.username} — {self.weight_kg}kg on {self.date}'


class ProgressPhoto(models.Model):
    CATEGORY_CHOICES = [
        ('Front', 'Front'), ('Side', 'Side'), ('Back', 'Back'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='progress_photos')
    date = models.DateField()
    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES)
    image = models.ImageField(upload_to='progress_photos/')
    weight_kg = models.FloatField(null=True, blank=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f'{self.user.username} — {self.category} photo on {self.date}'


class FitnessGoal(models.Model):
    CATEGORY_CHOICES = [
        ('exercise', 'Exercise'), ('weight', 'Weight'),
        ('nutrition', 'Nutrition'), ('workout', 'Workout'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='fitness_goals')
    title = models.CharField(max_length=120)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    target_value = models.FloatField()
    current_value = models.FloatField(default=0)
    unit = models.CharField(max_length=30)
    deadline = models.DateField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['deadline']

    @property
    def progress_percent(self):
        if self.target_value == 0:
            return 0
        return min(round((self.current_value / self.target_value) * 100, 1), 100)

    def __str__(self):
        return f'{self.user.username} — {self.title}'


class Achievement(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='achievements')
    title = models.CharField(max_length=120)
    description = models.TextField()
    category = models.CharField(max_length=60)
    icon_name = models.CharField(max_length=60, default='Trophy')
    unlocked = models.BooleanField(default=False)
    unlocked_at = models.DateTimeField(null=True, blank=True)
    progress = models.PositiveIntegerField(default=0)
    max_progress = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['-unlocked', 'title']

    def __str__(self):
        return f'{self.user.username} — {self.title} ({"✓" if self.unlocked else "locked"})'


class FitnessInsight(models.Model):
    TYPE_CHOICES = [
        ('strength', 'Strength'), ('nutrition', 'Nutrition'),
        ('training', 'Training'), ('volume', 'Volume'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='fitness_insights')
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    title = models.CharField(max_length=160)
    summary = models.CharField(max_length=255)
    detail = models.TextField()
    tag = models.CharField(max_length=60, blank=True)
    date = models.DateField()

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f'{self.user.username} — {self.title}'
