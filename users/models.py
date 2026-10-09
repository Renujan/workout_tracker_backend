from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    """Extended profile linked to Django's built-in User model."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')

    # Training stats
    current_streak = models.PositiveIntegerField(default=0)
    longest_streak = models.PositiveIntegerField(default=0)
    weekly_completion = models.FloatField(default=0.0, help_text='Percentage 0-100')
    weekly_workouts_target = models.PositiveIntegerField(default=4)
    weekly_workouts_completed = models.PositiveIntegerField(default=0)

    # Body stats
    current_weight_kg = models.FloatField(null=True, blank=True)
    target_weight_kg = models.FloatField(null=True, blank=True)
    training_since = models.DateField(null=True, blank=True)

    # Lifetime totals (denormalised for speed)
    total_workouts = models.PositiveIntegerField(default=0)
    total_volume_kg = models.FloatField(default=0.0)
    total_sets = models.PositiveIntegerField(default=0)
    total_prs = models.PositiveIntegerField(default=0)

    # Avatar
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'

    def __str__(self):
        return f'{self.user.username} — Profile'
