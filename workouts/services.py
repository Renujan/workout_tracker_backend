"""
Business logic services for workout tracking, session completion,
personal records (PR) detection, user statistics aggregation, and achievements.
"""

import datetime
from django.db import transaction
from django.utils import timezone
from users.models import UserProfile
from exercises.models import ExerciseHistory, PersonalRecord
from progress.models import Achievement
from .models import CompletedWorkout, WorkoutSet


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


def evaluate_and_unlock_achievements(user):
    """
    Evaluates milestone and consistency rules against user stats and unlocks achievements.
    """
    profile = getattr(user, 'profile', None)
    if not profile:
        profile, _ = UserProfile.objects.get_or_create(user=user)

    now = timezone.now()

    # Define rules: (title, description, category, icon, condition_fn, current_val_fn, max_prog)
    rules = [
        (
            'First Workout',
            'Log your first workout session',
            'milestone',
            'Dumbbell',
            profile.total_workouts >= 1,
            min(1, profile.total_workouts),
            1,
        ),
        (
            '10 Workouts',
            'Complete 10 workout sessions',
            'milestone',
            'Trophy',
            profile.total_workouts >= 10,
            min(10, profile.total_workouts),
            10,
        ),
        (
            'Century Club',
            'Lift 100kg+ on any compound exercise',
            'strength',
            'Zap',
            WorkoutSet.objects.filter(
                session_exercise__session__user=user,
                completed=True,
                weight_kg__gte=100,
            ).exists(),
            100 if WorkoutSet.objects.filter(
                session_exercise__session__user=user,
                completed=True,
                weight_kg__gte=100,
            ).exists() else 0,
            100,
        ),
        (
            'Iron Will — 7 Days',
            'Maintain a 7-day workout streak',
            'consistency',
            'Flame',
            profile.current_streak >= 7,
            min(7, profile.current_streak),
            7,
        ),
        (
            'PR Crusher',
            'Set 5 or more Personal Records',
            'strength',
            'Award',
            profile.total_prs >= 5,
            min(5, profile.total_prs),
            5,
        ),
    ]

    for title, desc, cat, icon, condition_met, cur_prog, max_prog in rules:
        achievement, created = Achievement.objects.get_or_create(
            user=user,
            title=title,
            defaults={
                'description': desc,
                'category': cat,
                'icon_name': icon,
                'max_progress': max_prog,
                'progress': cur_prog,
                'unlocked': False,
            },
        )
        if not achievement.unlocked:
            achievement.progress = cur_prog
            if condition_met:
                achievement.unlocked = True
                achievement.unlocked_at = now
                achievement.progress = max_prog
            achievement.save()


@transaction.atomic
def complete_workout_session(session):
    """
    Completes an active WorkoutSession, persists CompletedWorkout,
    updates user profile metrics, detects PRs, and updates achievements.
    """
    user = session.user
    session.is_completed = True
    session.completed_at = timezone.now()
    session.save(update_fields=['is_completed', 'completed_at'])

    # Compute total volume and sets from completed sets
    completed_sets = WorkoutSet.objects.filter(
        session_exercise__session=session, completed=True
    )
    total_volume = sum(s.weight_kg * s.reps for s in completed_sets)
    total_sets = completed_sets.count()
    duration_minutes = max(1, round(session.elapsed_seconds / 60))

    category = 'Full Body'
    if session.plan and session.plan.category:
        category = session.plan.category

    # Create or update CompletedWorkout
    completed_workout, _ = CompletedWorkout.objects.update_or_create(
        session=session,
        defaults={
            'user': user,
            'name': session.name,
            'category': category,
            'date': timezone.now().date(),
            'duration_minutes': duration_minutes,
            'total_volume_kg': round(total_volume, 2),
            'total_sets': total_sets,
        },
    )

    # Detect & Record PRs
    check_and_record_prs(user, session)

    # Recalculate User Profile stats & streaks
    update_user_profile_stats(user)

    # Check and unlock achievements
    evaluate_and_unlock_achievements(user)

    return completed_workout
