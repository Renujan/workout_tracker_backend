"""
Progress analytics and body composition trends services.
"""

from .models import BodyMeasurement

def calculate_body_composition_trends(user, height_cm=175.0):
    """
    Analyzes historical body measurements to produce trends, rate of weight change, and BMI.
    """
    measurements = list(BodyMeasurement.objects.filter(user=user).order_by('date'))
    height_m = max(1.0, float(height_cm) / 100.0)

    if not measurements:
        profile = getattr(user, 'profile', None)
        curr_w = profile.current_weight_kg if (profile and profile.current_weight_kg) else 75.0
        bmi = round(curr_w / (height_m ** 2), 1)
        return {
            'has_data': False,
            'current_weight_kg': curr_w,
            'bmi': bmi,
            'bmi_category': _get_bmi_category(bmi),
            'total_weight_delta_kg': 0.0,
            'body_fat_delta_percent': 0.0,
            'measurements_count': 0,
            'history': [],
        }

    first = measurements[0]
    latest = measurements[-1]

    weight_delta = round(latest.weight_kg - first.weight_kg, 1)

    bf_delta = 0.0
    if latest.body_fat_percent is not None and first.body_fat_percent is not None:
        bf_delta = round(latest.body_fat_percent - first.body_fat_percent, 1)

    days = max(1, (latest.date - first.date).days)
    weeks = days / 7.0
    rate_kg_per_week = round(weight_delta / weeks, 2) if weeks >= 1.0 else 0.0

    current_bmi = round(latest.weight_kg / (height_m ** 2), 1)

    history = [
        {
            'date': m.date.isoformat(),
            'weight_kg': m.weight_kg,
            'body_fat_percent': m.body_fat_percent,
            'bmi': round(m.weight_kg / (height_m ** 2), 1),
        }
        for m in measurements
    ]

    return {
        'has_data': True,
        'current_weight_kg': latest.weight_kg,
        'starting_weight_kg': first.weight_kg,
        'total_weight_delta_kg': weight_delta,
        'weekly_rate_kg': rate_kg_per_week,
        'current_body_fat_percent': latest.body_fat_percent,
        'body_fat_delta_percent': bf_delta,
        'current_bmi': current_bmi,
        'bmi_category': _get_bmi_category(current_bmi),
        'measurements_count': len(measurements),
        'history': history,
    }


def _get_bmi_category(bmi):
    if bmi < 18.5:
        return 'Underweight'
    elif bmi < 25.0:
        return 'Normal'
    elif bmi < 30.0:
        return 'Overweight'
    return 'Obese'


def evaluate_fitness_goals(user):
    """
    Evaluates and updates progress on all active FitnessGoals for a user.
    """
    from .models import FitnessGoal
    profile = getattr(user, 'profile', None)
    goals = FitnessGoal.objects.filter(user=user, is_completed=False)
    evaluated_count = 0

    for goal in goals:
        if goal.category == 'workout' and profile:
            goal.current_value = float(profile.total_workouts)
            if goal.current_value >= goal.target_value:
                goal.is_completed = True
            goal.save()
            evaluated_count += 1
        elif goal.category == 'weight' and profile and profile.current_weight_kg:
            goal.current_value = float(profile.current_weight_kg)
            # If target reached
            if goal.target_value <= goal.current_value and profile.target_weight_kg >= goal.target_value:
                goal.is_completed = True
    return evaluated_count


def evaluate_and_sync_achievements(user):
    """
    Evaluates global fitness milestones and syncs Achievement records for a user.
    """
    from django.utils import timezone
    from .models import Achievement
    profile = getattr(user, 'profile', None)

    total_workouts = profile.total_workouts if profile else 0
    total_volume = profile.total_volume_kg if profile else 0.0
    streak = profile.current_streak if profile else 0
    longest_streak = profile.longest_streak if profile else 0
    total_sets = profile.total_sets if profile else 0
    weekly_comp = profile.weekly_completion if profile else 0.0

    rules = [
        {
            'title': 'First Workout',
            'description': 'Completed your very first logged workout session.',
            'category': 'Milestone',
            'icon_name': 'Flame',
            'progress': min(1, total_workouts),
            'max_progress': 1,
            'is_met': total_workouts >= 1,
        },
        {
            'title': 'Consistency Champion',
            'description': 'Maintained a workout streak of at least 5 days.',
            'category': 'Streak',
            'icon_name': 'Zap',
            'progress': min(5, max(streak, longest_streak)),
            'max_progress': 5,
            'is_met': max(streak, longest_streak) >= 5,
        },
        {
            'title': 'Century Sets',
            'description': 'Completed 100 total exercise sets.',
            'category': 'Volume',
            'icon_name': 'Dumbbell',
            'progress': min(100, total_sets),
            'max_progress': 100,
            'is_met': total_sets >= 100,
        },
        {
            'title': 'Volume Titan',
            'description': 'Lifted an aggregate lifetime volume exceeding 10,000 kg.',
            'category': 'Volume',
            'icon_name': 'Trophy',
            'progress': min(10000, int(total_volume)),
            'max_progress': 10000,
            'is_met': total_volume >= 10000,
        },
        {
            'title': 'Perfect Week',
            'description': 'Hit 100% of your weekly target workouts.',
            'category': 'Consistency',
            'icon_name': 'Award',
            'progress': min(100, int(weekly_comp)),
            'max_progress': 100,
            'is_met': weekly_comp >= 100.0,
        },
    ]

    newly_unlocked = []
    total_unlocked = 0

    for rule in rules:
        ach, created = Achievement.objects.get_or_create(
            user=user,
            title=rule['title'],
            defaults={
                'description': rule['description'],
                'category': rule['category'],
                'icon_name': rule['icon_name'],
                'max_progress': rule['max_progress'],
                'progress': rule['progress'],
            }
        )

        ach.progress = rule['progress']
        ach.max_progress = rule['max_progress']

        if rule['is_met'] and not ach.unlocked:
            ach.unlocked = True
            ach.unlocked_at = timezone.now()
            newly_unlocked.append(ach.title)

        ach.save()
        if ach.unlocked:
            total_unlocked += 1

    return {
        'total_evaluated': len(rules),
        'total_unlocked': total_unlocked,
        'newly_unlocked': newly_unlocked,
    }

