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


def calculate_one_rep_max(weight_kg, reps, formula='epley'):
    """
    Computes estimated 1 Rep Max (1RM) and rep ranges using established lifting formulas.
    Supported formulas: 'epley', 'brzycki', 'lander', 'lombardi'.
    """
    if reps <= 0 or weight_kg <= 0:
        return {'estimated_1rm': 0.0, 'percentages': {}, 'rep_table': {}}

    if reps == 1:
        one_rm = float(weight_kg)
    elif formula == 'brzycki' and reps < 37:
        one_rm = weight_kg * (36.0 / (37.0 - reps))
    elif formula == 'lander' and reps < 38:
        one_rm = (100.0 * weight_kg) / (101.3 - 2.67123 * reps)
    elif formula == 'lombardi':
        one_rm = weight_kg * (reps ** 0.10)
    else:  # default 'epley'
        one_rm = weight_kg * (1.0 + reps / 30.0)

    one_rm = round(one_rm, 1)

    percentages = {
        f'{p}%': round(one_rm * (p / 100.0), 1)
        for p in [100, 95, 90, 85, 80, 75, 70, 65, 60, 50]
    }

    rep_table = {
        f'{r}RM': round(one_rm / (1.0 + r / 30.0), 1)
        for r in range(1, 13)
    }

    return {
        'weight_kg': float(weight_kg),
        'reps': int(reps),
        'formula': formula,
        'estimated_1rm': one_rm,
        'percentages': percentages,
        'rep_table': rep_table,
    }


def duplicate_workout_plan(user, plan_id, new_name=None):
    """
    Clones an existing WorkoutPlan including all associated PlanExercises.
    Assigns the cloned plan to the requesting user.
    """
    from .models import WorkoutPlan, PlanExercise
    plan = WorkoutPlan.objects.get(pk=plan_id, user=user)
    name = new_name or f'{plan.name} (Copy)'

    with transaction.atomic():
        new_plan = WorkoutPlan.objects.create(
            user=user,
            name=name,
            category=plan.category,
            estimated_minutes=plan.estimated_minutes,
            image_url=plan.image_url,
            is_active=False,
        )
        for pe in plan.exercises.all():
            PlanExercise.objects.create(
                plan=new_plan,
                exercise=pe.exercise,
                order=pe.order,
                target_sets=pe.target_sets,
                target_reps=pe.target_reps,
                target_weight_kg=pe.target_weight_kg,
            )
    return new_plan


def calculate_estimated_calories_burned(user, duration_minutes, total_volume_kg=0, category='Full Body'):
    """
    Estimates calories burned using standard MET (Metabolic Equivalent of Task) values.
    Formula: Calories = (MET * 3.5 * weight_kg / 200) * duration_minutes
    """
    profile = getattr(user, 'profile', None)
    weight_kg = profile.current_weight_kg if (profile and profile.current_weight_kg) else 75.0

    cat_lower = (category or '').lower()
    if 'cardio' in cat_lower:
        met = 7.5
    elif 'full' in cat_lower:
        met = 6.0
    else:
        met = 5.5

    base_calories = (met * 3.5 * weight_kg / 200.0) * max(1, duration_minutes)

    if total_volume_kg > 5000:
        base_calories *= 1.10
    elif total_volume_kg > 2500:
        base_calories *= 1.05

    return round(base_calories)




