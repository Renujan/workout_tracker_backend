from rest_framework import serializers
from .models import WorkoutPlan, PlanExercise, WorkoutSession, SessionExercise, WorkoutSet, CompletedWorkout


class PlanExerciseSerializer(serializers.ModelSerializer):
    exercise_name = serializers.CharField(source='exercise.name', read_only=True)
    muscle_group = serializers.CharField(source='exercise.muscle_group', read_only=True)

    class Meta:
        model = PlanExercise
        fields = ['id', 'exercise', 'exercise_name', 'muscle_group',
                  'order', 'target_sets', 'target_reps', 'target_weight_kg']


class WorkoutPlanSerializer(serializers.ModelSerializer):
    exercises = PlanExerciseSerializer(many=True, read_only=True)
    exercise_count = serializers.SerializerMethodField()
    estimated_sets = serializers.SerializerMethodField()

    class Meta:
        model = WorkoutPlan
        fields = ['id', 'name', 'category', 'estimated_minutes', 'image_url',
                  'is_active', 'exercises', 'exercise_count', 'estimated_sets', 'created_at']

    def get_exercise_count(self, obj):
        return obj.exercises.count()

    def get_estimated_sets(self, obj):
        return sum(e.target_sets for e in obj.exercises.all())


class WorkoutSetSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkoutSet
        fields = ['id', 'set_number', 'weight_kg', 'reps', 'rpe',
                  'completed', 'is_pr', 'target_weight_kg', 'target_reps']


class SessionExerciseSerializer(serializers.ModelSerializer):
    sets = WorkoutSetSerializer(many=True, read_only=True)
    exercise_name = serializers.CharField(source='exercise.name', read_only=True)
    muscle_group = serializers.CharField(source='exercise.muscle_group', read_only=True)

    class Meta:
        model = SessionExercise
        fields = ['id', 'exercise', 'exercise_name', 'muscle_group',
                  'order', 'previous_performance', 'sets']


class WorkoutSessionSerializer(serializers.ModelSerializer):
    exercises = SessionExerciseSerializer(many=True, read_only=True)

    class Meta:
        model = WorkoutSession
        fields = ['id', 'plan', 'name', 'started_at', 'elapsed_seconds',
                  'is_completed', 'completed_at', 'exercises']


class CompletedWorkoutSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompletedWorkout
        fields = ['id', 'session', 'name', 'category', 'date',
                  'duration_minutes', 'total_volume_kg', 'total_sets']
