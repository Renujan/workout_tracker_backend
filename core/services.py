"""
Core export and portability services.
"""
from django.utils import timezone
from typing import Dict, Any


class UserArchiveExportService:
    """Aggregates all user health and fitness data across apps into a unified export package."""

    @classmethod
    def export_all_user_data(cls, user) -> Dict[str, Any]:
        from workouts.models import CompletedWorkout
        from exercises.models import PersonalRecord
        from nutrition.models import MealItem, DailyNutrition
        from progress.models import BodyMeasurement, FitnessGoal, Achievement

        # 1. Profile
        profile_data = None
        if hasattr(user, 'profile') and user.profile:
            p = user.profile
            profile_data = {
                'current_weight_kg': p.current_weight_kg,
                'target_weight_kg': p.target_weight_kg,
                'current_streak': p.current_streak,
                'longest_streak': p.longest_streak,
                'total_workouts': p.total_workouts,
                'total_volume_kg': p.total_volume_kg,
                'total_sets': p.total_sets,
                'total_prs': p.total_prs,
                'weekly_workouts_target': p.weekly_workouts_target,
            }

        # 2. Workouts
        workouts = list(CompletedWorkout.objects.filter(user=user).order_by('-date').values(
            'date', 'name', 'category', 'duration_minutes', 'total_volume_kg', 'total_sets'
        ))

        # 3. Personal Records
        prs = list(PersonalRecord.objects.filter(user=user).select_related('exercise').values(
            'exercise__name', 'weight_kg', 'reps', 'date', 'category', 'improvement_kg'
        ))

        # 4. Nutrition
        meals = list(MealItem.objects.filter(user=user).order_by('-date').values(
            'date', 'category', 'name', 'calories', 'protein_grams', 'carbs_grams', 'fat_grams'
        ))
        daily_nutrition = list(DailyNutrition.objects.filter(user=user).order_by('-date').values(
            'date', 'calories', 'protein_grams', 'carbs_grams', 'fat_grams', 'water_liters'
        ))

        # 5. Progress
        measurements = list(BodyMeasurement.objects.filter(user=user).order_by('-date').values(
            'date', 'weight_kg', 'body_fat_percent', 'chest_cm', 'waist_cm', 'arms_cm', 'thighs_cm'
        ))
        goals = list(FitnessGoal.objects.filter(user=user).values(
            'title', 'category', 'target_value', 'current_value', 'unit', 'is_completed'
        ))
        achievements = list(Achievement.objects.filter(user=user, unlocked=True).values(
            'title', 'description', 'category', 'unlocked_at'
        ))

        return {
            'export_metadata': {
                'generated_at': timezone.now().isoformat(),
                'export_version': '1.0',
                'user_id': user.id,
                'username': user.username,
                'email': user.email,
            },
            'profile': profile_data,
            'workouts_count': len(workouts),
            'workouts': workouts,
            'personal_records': prs,
            'nutrition': {
                'meals': meals,
                'daily_summaries': daily_nutrition,
            },
            'progress': {
                'body_measurements': measurements,
                'fitness_goals': goals,
                'unlocked_achievements': achievements,
            }
        }
