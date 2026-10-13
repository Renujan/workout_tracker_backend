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


def get_weekly_workout_summary(user, reference_date=None):
    """
    Aggregates workout statistics for the week containing reference_date (defaults to today).
    Week boundaries: Monday to Sunday.
    """
    ref_date = reference_date or timezone.now().date()
    monday = ref_date - datetime.timedelta(days=ref_date.weekday())
    sunday = monday + datetime.timedelta(days=6)

    weekly_workouts = CompletedWorkout.objects.filter(
        user=user, date__gte=monday, date__lte=sunday
    )

    total_volume = sum(w.total_volume_kg for w in weekly_workouts)
    total_minutes = sum(w.duration_minutes for w in weekly_workouts)
    total_sets = sum(w.total_sets for w in weekly_workouts)
    count = weekly_workouts.count()

    active_days = sorted(list(set(w.date.strftime('%a') for w in weekly_workouts)))
    categories = {}
    for w in weekly_workouts:
        cat = w.category or 'Other'
        categories[cat] = categories.get(cat, 0) + 1

    profile = getattr(user, 'profile', None)
    target = profile.weekly_workouts_target if profile else 4
    adherence = round((count / max(1, target)) * 100, 1) if target else 0.0

    return {
        'week_start': monday.isoformat(),
        'week_end': sunday.isoformat(),
        'workouts_completed': count,
        'weekly_workouts_target': target,
        'adherence_percentage': min(100.0, adherence),
        'total_volume_kg': round(total_volume, 1),
        'total_duration_minutes': total_minutes,
        'total_sets': total_sets,
        'active_days': active_days,
        'category_breakdown': categories,
    }


def export_workout_history(user, export_format='json'):
    """
    Exports all completed workouts for the user in either JSON or CSV format.
    """
    import csv
    import io
    workouts = CompletedWorkout.objects.filter(user=user).order_by('-date')

    data = []
    for w in workouts:
        data.append({
            'date': w.date.isoformat(),
            'name': w.name,
            'category': w.category,
            'duration_minutes': w.duration_minutes,
            'total_volume_kg': w.total_volume_kg,
            'total_sets': w.total_sets,
        })

    if export_format.lower() == 'csv':
        output = io.StringIO()
        writer = csv.DictWriter(
            output,
            fieldnames=['date', 'name', 'category', 'duration_minutes', 'total_volume_kg', 'total_sets']
        )
        writer.writeheader()
        writer.writerows(data)
        return output.getvalue(), 'text/csv'

    return data, 'application/json'


def calculate_recommended_rest_timer(reps=None, exercise_type='compound'):
    """
    Calculates recommended rest interval in seconds based on exercise type and rep ranges.
    Strength (1-5 reps): 180s (3m)
    Hypertrophy (6-12 reps): 90s (1m 30s)
    Endurance (13+ reps): 45s
    Compound exercises add +30s.
    """
    r = int(reps) if reps is not None else 8
    is_compound = str(exercise_type).lower() in ['compound', 'true', '1']

    if r <= 5:
        base_rest = 180
        min_rest = 120
        max_rest = 300
        goal = 'Strength & Power'
        tip = 'Heavy loads require full phosphocreatine replenishment between sets.'
    elif r <= 12:
        base_rest = 90
        min_rest = 60
        max_rest = 120
        goal = 'Hypertrophy'
        tip = 'Moderate rest balances metabolic stress and mechanical tension.'
    else:
        base_rest = 45
        min_rest = 30
        max_rest = 60
        goal = 'Muscular Endurance'
        tip = 'Short rest trains muscle buffering capacity and stamina.'

    if is_compound:
        base_rest += 30

    minutes = base_rest // 60
    seconds = base_rest % 60
    formatted = f"{minutes}m {seconds:02d}s" if minutes > 0 else f"{seconds}s"

    return {
        'target_reps': r,
        'exercise_type': 'compound' if is_compound else 'isolation',
        'recommended_rest_seconds': base_rest,
        'recommended_rest_formatted': formatted,
        'min_rest_seconds': min_rest,
        'max_rest_seconds': max_rest,
        'training_goal': goal,
        'tip': tip,
    }


def get_workout_activity_calendar(user, days=30):
    """
    Builds a day-by-day activity heatmap and consistency metrics for the last N days.
    """
    days = min(max(int(days), 7), 365)
    today = timezone.now().date()
    start_date = today - datetime.timedelta(days=days - 1)

    workouts = CompletedWorkout.objects.filter(
        user=user, date__gte=start_date, date__lte=today
    ).order_by('date')

    # Group by date
    daily_stats = {}
    for w in workouts:
        d_str = w.date.isoformat()
        if d_str not in daily_stats:
            daily_stats[d_str] = {'workouts': 0, 'volume_kg': 0.0, 'duration_minutes': 0, 'categories': []}
        daily_stats[d_str]['workouts'] += 1
        daily_stats[d_str]['volume_kg'] += w.total_volume_kg
        daily_stats[d_str]['duration_minutes'] += w.duration_minutes
        if w.category and w.category not in daily_stats[d_str]['categories']:
            daily_stats[d_str]['categories'].append(w.category)

    heatmap = []
    active_days_count = 0
    total_volume = 0.0
    for i in range(days):
        current_day = start_date + datetime.timedelta(days=i)
        d_str = current_day.isoformat()
        day_data = daily_stats.get(d_str)
        if day_data:
            active_days_count += 1
            vol = round(day_data['volume_kg'], 1)
            total_volume += vol
            # Level 1-4
            if vol > 5000:
                level = 4
            elif vol > 2500:
                level = 3
            elif vol > 1000:
                level = 2
            else:
                level = 1

            heatmap.append({
                'date': d_str,
                'active': True,
                'level': level,
                'workout_count': day_data['workouts'],
                'volume_kg': vol,
                'duration_minutes': day_data['duration_minutes'],
                'categories': day_data['categories'],
            })
        else:
            heatmap.append({
                'date': d_str,
                'active': False,
                'level': 0,
                'workout_count': 0,
                'volume_kg': 0.0,
                'duration_minutes': 0,
                'categories': [],
            })

    current_streak = calculate_user_streaks(user)
    profile = getattr(user, 'profile', None)
    longest_streak = profile.longest_streak if profile else current_streak

    return {
        'days_requested': days,
        'start_date': start_date.isoformat(),
        'end_date': today.isoformat(),
        'active_days_count': active_days_count,
        'consistency_rate_pct': round((active_days_count / days) * 100, 1),
        'total_period_volume_kg': round(total_volume, 1),
        'current_streak': current_streak,
        'longest_streak': longest_streak,
        'calendar': heatmap,
    }


def calculate_volume_progression(user, weeks=4):
    """
    Computes week-over-week training tonnage volume progression across the last N weeks.
    Classifies trend into Progressive Overload, Maintenance, or Deload.
    """
    weeks = min(max(int(weeks), 2), 12)
    today = timezone.now().date()
    current_monday = today - datetime.timedelta(days=today.weekday())

    weekly_data = []
    for i in range(weeks - 1, -1, -1):
        w_start = current_monday - datetime.timedelta(weeks=i)
        w_end = w_start + datetime.timedelta(days=6)

        week_workouts = CompletedWorkout.objects.filter(
            user=user, date__gte=w_start, date__lte=w_end
        )
        vol = round(sum(w.total_volume_kg for w in week_workouts), 1)
        count = week_workouts.count()
        sets = sum(w.total_sets for w in week_workouts)

        weekly_data.append({
            'week_index': len(weekly_data) + 1,
            'start_date': w_start.isoformat(),
            'end_date': w_end.isoformat(),
            'total_volume_kg': vol,
            'workout_count': count,
            'total_sets': sets,
            'percentage_change': 0.0,
        })

    # Calculate WoW changes
    for i in range(1, len(weekly_data)):
        prev_vol = weekly_data[i - 1]['total_volume_kg']
        curr_vol = weekly_data[i]['total_volume_kg']
        if prev_vol > 0:
            diff = ((curr_vol - prev_vol) / prev_vol) * 100.0
            weekly_data[i]['percentage_change'] = round(diff, 1)
        elif curr_vol > 0:
            weekly_data[i]['percentage_change'] = 100.0

    curr_vol = weekly_data[-1]['total_volume_kg']
    prev_vol = weekly_data[-2]['total_volume_kg'] if len(weekly_data) >= 2 else curr_vol
    wow_change = weekly_data[-1]['percentage_change']

    if wow_change > 5.0:
        trend = 'Progressive Overload'
    elif wow_change < -15.0:
        trend = 'Deload / Recovery'
    else:
        trend = 'Maintenance'

    return {
        'weeks_evaluated': weeks,
        'current_week_volume_kg': curr_vol,
        'previous_week_volume_kg': prev_vol,
        'wow_change_percentage': wow_change,
        'training_trend': trend,
        'weekly_history': weekly_data,
    }
