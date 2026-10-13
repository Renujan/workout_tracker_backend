"""
Exercise and personal record analytics service.
"""
from typing import Dict, Any, Optional
from django.db.models import Max
from .models import Exercise, ExerciseHistory, PersonalRecord


class PersonalRecordService:
    """Service to look up personal records, calculate PR progression, and aggregate records."""

    @classmethod
    def get_exercise_pr_detail(cls, user, exercise: Exercise) -> Dict[str, Any]:
        """Fetch all-time bests (max weight, max reps, max volume, best 1RM) for a specific exercise."""
        history_qs = ExerciseHistory.objects.filter(user=user, exercise=exercise)
        records_qs = PersonalRecord.objects.filter(user=user, exercise=exercise)

        max_weight_record = records_qs.order_by('-weight_kg').first()
        max_reps_record = records_qs.order_by('-reps').first()

        max_volume = history_qs.aggregate(Max('volume_kg'))['volume_kg__max'] or 0.0
        best_1rm = history_qs.aggregate(Max('estimated_1rm'))['estimated_1rm__max'] or 0.0

        latest_pr = records_qs.order_by('-date').first()

        return {
            'exercise_id': exercise.id,
            'exercise_name': exercise.name,
            'muscle_group': exercise.muscle_group,
            'max_weight_kg': max_weight_record.weight_kg if max_weight_record else None,
            'max_weight_reps': max_weight_record.reps if max_weight_record else None,
            'max_reps': max_reps_record.reps if max_reps_record else None,
            'max_volume_kg': round(max_volume, 2),
            'best_estimated_1rm': round(best_1rm, 2),
            'latest_pr_date': str(latest_pr.date) if latest_pr else None,
            'has_records': records_qs.exists() or history_qs.exists(),
        }

    @classmethod
    def get_user_pr_overview(cls, user) -> Dict[str, Any]:
        """Aggregate PR stats across all exercises for the user."""
        records_qs = PersonalRecord.objects.filter(user=user).select_related('exercise')
        total_count = records_qs.count()
        recent_records = records_qs.order_by('-date')[:5]

        recent_data = [
            {
                'id': pr.id,
                'exercise': pr.exercise.name,
                'muscle_group': pr.exercise.muscle_group,
                'weight_kg': pr.weight_kg,
                'reps': pr.reps,
                'improvement_kg': pr.improvement_kg,
                'date': str(pr.date),
                'category': pr.category,
            }
            for pr in recent_records
        ]

        return {
            'total_prs': total_count,
            'recent_prs': recent_data,
        }
