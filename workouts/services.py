"""
Business logic services for workout tracking, session completion,
personal records (PR) detection, user statistics aggregation, and achievements.
"""

import datetime
from django.db import transaction
from django.utils import timezone
from users.models import UserProfile
from exercises.models import ExerciseHistory, PersonalRecord
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


def check_and_record_prs(user, session):
    """
    Inspects completed sets in a session to identify if any Personal Records were broken.
    Creates PersonalRecord instances and updates ExerciseHistory accordingly.
    Returns list of newly created PRs.
    """
    today = timezone.now().date()
    new_prs = []

    for se in session.exercises.all():
        completed_sets = se.sets.filter(completed=True)
        if not completed_sets.exists():
            continue

        # Find best set by weight lifted
        best_set = completed_sets.order_by('-weight_kg', '-reps').first()
        if not best_set or best_set.weight_kg <= 0:
            continue

        # Look up existing best strength PR
        existing_pr = (
            PersonalRecord.objects.filter(
                user=user, exercise=se.exercise, category='strength'
            )
            .order_by('-weight_kg')
            .first()
        )

        is_new_pr = False
        prev_weight = 0.0
        prev_reps = 0
        improvement = best_set.weight_kg

        if not existing_pr:
            is_new_pr = True
        elif best_set.weight_kg > existing_pr.weight_kg:
            is_new_pr = True
            prev_weight = existing_pr.weight_kg
            prev_reps = existing_pr.reps
            improvement = round(best_set.weight_kg - existing_pr.weight_kg, 2)

        if is_new_pr:
            pr = PersonalRecord.objects.create(
                user=user,
                exercise=se.exercise,
                weight_kg=best_set.weight_kg,
                reps=best_set.reps,
                previous_weight_kg=prev_weight,
                previous_reps=prev_reps,
                improvement_kg=improvement,
                date=today,
                category='strength',
            )
            best_set.is_pr = True
            best_set.save(update_fields=['is_pr'])
            new_prs.append(pr)

        # Update ExerciseHistory entry for today
        ExerciseHistory.objects.update_or_create(
            user=user,
            exercise=se.exercise,
            date=today,
            defaults={
                'weight_kg': best_set.weight_kg,
                'reps': best_set.reps,
            },
        )

    return new_prs
