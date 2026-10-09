from django.db import models
from django.contrib.auth.models import User
from exercises.models import Exercise


class WorkoutPlan(models.Model):
    CATEGORY_CHOICES = [
        ('Push', 'Push'), ('Pull', 'Pull'), ('Legs', 'Legs'),
        ('Upper', 'Upper'), ('Lower', 'Lower'), ('Full Body', 'Full Body'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='workout_plans')
    name = models.CharField(max_length=120)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    estimated_minutes = models.PositiveIntegerField(default=60)
    image_url = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.username} — {self.name}'


class PlanExercise(models.Model):
    """An exercise slot within a WorkoutPlan."""
    plan = models.ForeignKey(WorkoutPlan, on_delete=models.CASCADE, related_name='exercises')
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)
    order = models.PositiveSmallIntegerField(default=0)
    target_sets = models.PositiveSmallIntegerField(default=3)
    target_reps = models.CharField(max_length=20, default='8-12')
    target_weight_kg = models.FloatField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f'{self.plan.name} — {self.exercise.name}'


class WorkoutSession(models.Model):
    """An active (in-progress) workout session."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='workout_sessions')
    plan = models.ForeignKey(WorkoutPlan, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=120)
    started_at = models.DateTimeField(auto_now_add=True)
    elapsed_seconds = models.PositiveIntegerField(default=0)
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-started_at']

    def __str__(self):
        return f'{self.user.username} — {self.name} ({"done" if self.is_completed else "active"})'


class SessionExercise(models.Model):
    """An exercise instance within an active session."""
    session = models.ForeignKey(WorkoutSession, on_delete=models.CASCADE, related_name='exercises')
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)
    order = models.PositiveSmallIntegerField(default=0)
    previous_performance = models.CharField(max_length=60, blank=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f'{self.session} — {self.exercise.name}'


class WorkoutSet(models.Model):
    """A single set within a SessionExercise."""
    session_exercise = models.ForeignKey(SessionExercise, on_delete=models.CASCADE, related_name='sets')
    set_number = models.PositiveSmallIntegerField()
    weight_kg = models.FloatField(default=0)
    reps = models.PositiveSmallIntegerField(default=0)
    rpe = models.FloatField(null=True, blank=True, help_text='Rate of Perceived Exertion 1-10')
    completed = models.BooleanField(default=False)
    is_pr = models.BooleanField(default=False)
    target_weight_kg = models.FloatField(null=True, blank=True)
    target_reps = models.CharField(max_length=20, blank=True)

    class Meta:
        ordering = ['set_number']

    def __str__(self):
        return f'Set {self.set_number}: {self.weight_kg}kg x {self.reps}'


class CompletedWorkout(models.Model):
    """A finalized summary of a completed session."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='completed_workouts')
    session = models.OneToOneField(WorkoutSession, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=120)
    category = models.CharField(max_length=40, blank=True)
    date = models.DateField()
    duration_minutes = models.PositiveIntegerField(default=0)
    total_volume_kg = models.FloatField(default=0)
    total_sets = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f'{self.user.username} — {self.name} on {self.date}'
