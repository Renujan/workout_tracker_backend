from rest_framework import serializers
from .models import Exercise, ExerciseHistory, PersonalRecord


class ExerciseHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ExerciseHistory
        fields = ['id', 'date', 'weight_kg', 'reps', 'volume_kg', 'estimated_1rm']
        read_only_fields = ['volume_kg', 'estimated_1rm']


class ExerciseSerializer(serializers.ModelSerializer):
    history = ExerciseHistorySerializer(many=True, read_only=True)

    class Meta:
        model = Exercise
        fields = [
            'id', 'name', 'muscle_group', 'equipment', 'difficulty',
            'description', 'image_url', 'history', 'created_at',
        ]


class PersonalRecordSerializer(serializers.ModelSerializer):
    exercise_name = serializers.CharField(source='exercise.name', read_only=True)

    class Meta:
        model = PersonalRecord
        fields = [
            'id', 'exercise', 'exercise_name', 'weight_kg', 'reps',
            'previous_weight_kg', 'previous_reps', 'improvement_kg',
            'date', 'category',
        ]
