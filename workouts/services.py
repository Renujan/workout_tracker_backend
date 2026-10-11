"""
Business logic services for workout tracking, session completion,
personal records (PR) detection, user statistics aggregation, and achievements.
"""

import datetime
from django.db import transaction
from django.utils import timezone
from users.models import UserProfile
from exercises.models import PersonalRecord
from .models import CompletedWorkout


def calculate_user_streaks(user):
    """
    Calculates the current streak of consecutive workout days for a user.
    """
    workout_dates = set(
        CompletedWorkout.objects.filter(user=user)
        .values_list('date', flat=True)
    )
    if not workout_dates:
        return 0

    today = timezone.now().date()
    current_date = today

    # If the user hasn't worked out yet today, start streak check from yesterday
    if current_date not in workout_dates:
        current_date -= datetime.timedelta(days=1)

    current_streak = 0
    while current_date in workout_dates:
        current_streak += 1
        current_date -= datetime.timedelta(days=1)

    return current_streak


def update_user_profile_stats(user, added_volume_kg=0, added_sets=0):
    """
    Recalculates lifetime totals, streaks, and weekly completion metrics on UserProfile.
    """
    profile, _ = UserProfile.objects.get_or_create(user=user)

    # Lifetime workouts, volume, and sets
    all_workouts = CompletedWorkout.objects.filter(user=user)
    profile.total_workouts = all_workouts.count()
    profile.total_volume_kg = sum(w.total_volume_kg for w in all_workouts)
    profile.total_sets = sum(w.total_sets for w in all_workouts)

    # PR count
    profile.total_prs = PersonalRecord.objects.filter(user=user).count()

    # Streaks
    curr_streak = calculate_user_streaks(user)
    profile.current_streak = curr_streak
    if curr_streak > profile.longest_streak:
        profile.longest_streak = curr_streak

    # Weekly targets (Monday to Sunday)
    today = timezone.now().date()
    start_of_week = today - datetime.timedelta(days=today.weekday())
    weekly_completed = CompletedWorkout.objects.filter(
        user=user, date__gte=start_of_week, date__lte=today
    ).count()

    profile.weekly_workouts_completed = weekly_completed
    if profile.weekly_workouts_target > 0:
        profile.weekly_completion = min(
            100.0,
            round((weekly_completed / profile.weekly_workouts_target) * 100.0, 1),
        )

    profile.save()
    return profile
