from rest_framework import serializers
from exercises.models import Exercise
from .models import WorkoutPlan, PlanExercise, WorkoutSession, SessionExercise, WorkoutSet, CompletedWorkout


class PlanExerciseSerializer(serializers.ModelSerializer):
    exercise_name = serializers.CharField(source='exercise.name', read_only=True)
    muscle_group = serializers.CharField(source='exercise.muscle_group', read_only=True)
    exercise = serializers.PrimaryKeyRelatedField(queryset=Exercise.objects.all())

    class Meta:
        model = PlanExercise
        fields = [
            'id', 'exercise', 'exercise_name', 'muscle_group',
            'order', 'target_sets', 'target_reps', 'target_weight_kg'
        ]


class WorkoutPlanSerializer(serializers.ModelSerializer):
    exercises = PlanExerciseSerializer(many=True, required=False)
    exercise_count = serializers.SerializerMethodField()
    estimated_sets = serializers.SerializerMethodField()

    class Meta:
        model = WorkoutPlan
        fields = [
            'id', 'name', 'category', 'estimated_minutes', 'image_url',
            'is_active', 'exercises', 'exercise_count', 'estimated_sets', 'created_at'
        ]

    def get_exercise_count(self, obj):
        return obj.exercises.count()

    def get_estimated_sets(self, obj):
        return sum(e.target_sets for e in obj.exercises.all())

    def create(self, validated_data):
        exercises_data = validated_data.pop('exercises', [])
        plan = WorkoutPlan.objects.create(**validated_data)
        for idx, ex_data in enumerate(exercises_data):
            if 'order' not in ex_data:
                ex_data['order'] = idx
            PlanExercise.objects.create(plan=plan, **ex_data)
        return plan

    def update(self, instance, validated_data):
        exercises_data = validated_data.pop('exercises', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if exercises_data is not None:
            instance.exercises.all().delete()
            for idx, ex_data in enumerate(exercises_data):
                if 'order' not in ex_data:
                    ex_data['order'] = idx
                PlanExercise.objects.create(plan=instance, **ex_data)
        return instance


class WorkoutSetSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkoutSet
        fields = [
            'id', 'session_exercise', 'set_number', 'weight_kg', 'reps', 'rpe',
            'completed', 'is_pr', 'target_weight_kg', 'target_reps'
        ]
        extra_kwargs = {
            'session_exercise': {'required': False, 'read_only': True}
        }


class SessionExerciseSerializer(serializers.ModelSerializer):
    sets = WorkoutSetSerializer(many=True, required=False)
    exercise_name = serializers.CharField(source='exercise.name', read_only=True)
    muscle_group = serializers.CharField(source='exercise.muscle_group', read_only=True)
    exercise = serializers.PrimaryKeyRelatedField(queryset=Exercise.objects.all())

    class Meta:
        model = SessionExercise
        fields = [
            'id', 'exercise', 'exercise_name', 'muscle_group',
            'order', 'previous_performance', 'sets'
        ]


class WorkoutSessionSerializer(serializers.ModelSerializer):
    exercises = SessionExerciseSerializer(many=True, required=False)

    class Meta:
        model = WorkoutSession
        fields = [
            'id', 'plan', 'name', 'started_at', 'elapsed_seconds',
            'is_completed', 'completed_at', 'exercises'
        ]

    def create(self, validated_data):
        exercises_data = validated_data.pop('exercises', [])
        plan = validated_data.get('plan', None)
        session = WorkoutSession.objects.create(**validated_data)

        if exercises_data:
            for idx, ex_data in enumerate(exercises_data):
                sets_data = ex_data.pop('sets', [])
                if 'order' not in ex_data:
                    ex_data['order'] = idx
                session_ex = SessionExercise.objects.create(session=session, **ex_data)
                for s_idx, set_data in enumerate(sets_data, start=1):
                    if 'set_number' not in set_data:
                        set_data['set_number'] = s_idx
                    WorkoutSet.objects.create(session_exercise=session_ex, **set_data)
        elif plan:
            # Auto-populate session exercises & sets from plan template
            for pe in plan.exercises.all().order_by('order'):
                se = SessionExercise.objects.create(
                    session=session,
                    exercise=pe.exercise,
                    order=pe.order,
                    previous_performance='',
                )
                for s_idx in range(1, pe.target_sets + 1):
                    WorkoutSet.objects.create(
                        session_exercise=se,
                        set_number=s_idx,
                        weight_kg=pe.target_weight_kg,
                        reps=0,
                        completed=False,
                        target_weight_kg=pe.target_weight_kg,
                        target_reps=pe.target_reps,
                    )
        return session

    def update(self, instance, validated_data):
        exercises_data = validated_data.pop('exercises', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if exercises_data is not None:
            instance.exercises.all().delete()
            for idx, ex_data in enumerate(exercises_data):
                sets_data = ex_data.pop('sets', [])
                if 'order' not in ex_data:
                    ex_data['order'] = idx
                session_ex = SessionExercise.objects.create(session=instance, **ex_data)
                for s_idx, set_data in enumerate(sets_data, start=1):
                    if 'set_number' not in set_data:
                        set_data['set_number'] = s_idx
                    WorkoutSet.objects.create(session_exercise=session_ex, **set_data)
        return instance


class CompletedWorkoutSerializer(serializers.ModelSerializer):
    exercises = serializers.SerializerMethodField()

    class Meta:
        model = CompletedWorkout
        fields = [
            'id', 'session', 'name', 'category', 'date',
            'duration_minutes', 'total_volume_kg', 'total_sets', 'exercises'
        ]

    def get_exercises(self, obj):
        if obj.session:
            result = []
            for se in obj.session.exercises.all().prefetch_related('sets'):
                completed_sets = se.sets.filter(completed=True)
                if completed_sets.exists():
                    max_w = max((s.weight_kg for s in completed_sets), default=0)
                    result.append({
                        'name': se.exercise.name,
                        'sets': completed_sets.count(),
                        'max_weight_kg': max_w,
                    })
            return result
        return []
