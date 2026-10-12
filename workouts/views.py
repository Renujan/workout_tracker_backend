from rest_framework.views import APIView
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from exercises.models import Exercise

from .models import (
    WorkoutPlan, WorkoutSession, SessionExercise,
    WorkoutSet, CompletedWorkout
)
from .serializers import (
    WorkoutPlanSerializer, WorkoutSessionSerializer,
    CompletedWorkoutSerializer, WorkoutSetSerializer
)
from .services import (
    complete_workout_session, update_user_profile_stats,
    evaluate_and_unlock_achievements, calculate_one_rep_max,
    duplicate_workout_plan, calculate_estimated_calories_burned
)




class WorkoutPlanViewSet(viewsets.ModelViewSet):
    """CRUD for the user's workout plans."""
    serializer_class = WorkoutPlanSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['category', 'is_active']
    search_fields = ['name']

    def get_queryset(self):
        return WorkoutPlan.objects.filter(user=self.request.user).prefetch_related('exercises')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def duplicate(self, request, pk=None):
        """POST /api/v1/workouts/plans/{id}/duplicate/ — clone plan and its exercises."""
        plan = self.get_object()
        new_name = request.data.get('name')
        new_plan = duplicate_workout_plan(request.user, plan.id, new_name=new_name)
        serializer = self.get_serializer(new_plan)
        return Response(serializer.data, status=status.HTTP_201_CREATED)



class WorkoutSessionViewSet(viewsets.ModelViewSet):
    """CRUD for active workout sessions."""
    serializer_class = WorkoutSessionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['is_completed']
    ordering_fields = ['started_at']

    def get_queryset(self):
        return WorkoutSession.objects.filter(user=self.request.user).prefetch_related(
            'exercises__sets'
        )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'], url_path='active')
    def get_active(self, request):
        """GET /api/v1/workouts/sessions/active/ — returns current active session if any."""
        active_session = self.get_queryset().filter(is_completed=False).order_by('-started_at').first()
        if not active_session:
            return Response(None, status=status.HTTP_200_OK)
        return Response(self.get_serializer(active_session).data)

    @action(detail=True, methods=['post'], url_path='complete')
    def complete(self, request, pk=None):
        """
        POST /api/v1/workouts/sessions/{id}/complete/
        Finalizes active workout, calculates volume/PRs, unlocks achievements, and returns summary.
        """
        session = self.get_object()
        completed_workout = complete_workout_session(session)
        return Response(
            CompletedWorkoutSerializer(completed_workout).data,
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'], url_path='add-exercise')
    def add_exercise(self, request, pk=None):
        """
        POST /api/v1/workouts/sessions/{id}/add-exercise/
        Adds a new exercise dynamically to an in-progress session.
        Payload: { "exercise": <id>, "target_sets": 3, "target_weight_kg": 60, "target_reps": "8-12" }
        """
        session = self.get_object()
        exercise_id = request.data.get('exercise')
        target_sets = int(request.data.get('target_sets', 3))
        target_weight = float(request.data.get('target_weight_kg', 0))
        target_reps = str(request.data.get('target_reps', '8-12'))

        try:
            exercise = Exercise.objects.get(id=exercise_id)
        except Exercise.DoesNotExist:
            return Response({'detail': 'Exercise not found.'}, status=status.HTTP_404_NOT_FOUND)

        order = session.exercises.count()
        session_ex = SessionExercise.objects.create(
            session=session,
            exercise=exercise,
            order=order,
        )

        for s_num in range(1, target_sets + 1):
            WorkoutSet.objects.create(
                session_exercise=session_ex,
                set_number=s_num,
                weight_kg=target_weight,
                reps=0,
                completed=False,
                target_weight_kg=target_weight,
                target_reps=target_reps,
            )

        return Response(self.get_serializer(session).data, status=status.HTTP_201_CREATED)


class WorkoutSetViewSet(viewsets.ModelViewSet):
    """
    Direct CRUD for sets within active workout sessions.
    Enables instant set updates (weight, reps, RPE, completed status) during workouts.
    """
    serializer_class = WorkoutSetSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return WorkoutSet.objects.filter(
            session_exercise__session__user=self.request.user
        )


class CompletedWorkoutViewSet(viewsets.ModelViewSet):
    """CRUD for completed workout summaries (history)."""
    serializer_class = CompletedWorkoutSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['category']
    ordering_fields = ['date', 'total_volume_kg']

    def get_queryset(self):
        return CompletedWorkout.objects.filter(user=self.request.user).prefetch_related(
            'session__exercises__sets', 'session__exercises__exercise'
        )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
        update_user_profile_stats(self.request.user)
        evaluate_and_unlock_achievements(self.request.user)


class OneRepMaxCalculatorView(APIView):
    """POST /api/v1/workouts/calculator/1rm/ — calculate estimated 1RM, percentages and rep table."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        weight = request.data.get('weight_kg')
        reps = request.data.get('reps')
        formula = request.data.get('formula', 'epley')

        if weight is None or reps is None:
            return Response(
                {'error': 'Both weight_kg and reps are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            weight = float(weight)
            reps = int(reps)
        except (ValueError, TypeError):
            return Response(
                {'error': 'Invalid weight_kg or reps format.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        result = calculate_one_rep_max(weight, reps, formula=formula)
        return Response(result, status=status.HTTP_200_OK)


class CalorieEstimateView(APIView):
    """POST /api/v1/workouts/calculator/calories/ — estimate calories burned."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        duration = request.data.get('duration_minutes')
        total_volume = request.data.get('total_volume_kg', 0)
        category = request.data.get('category', 'Full Body')

        if duration is None:
            return Response(
                {'error': 'duration_minutes is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            duration = int(duration)
            total_volume = float(total_volume)
        except (ValueError, TypeError):
            return Response(
                {'error': 'Invalid format for duration or total_volume.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        calories = calculate_estimated_calories_burned(
            user=request.user,
            duration_minutes=duration,
            total_volume_kg=total_volume,
            category=category
        )
        return Response({
            'duration_minutes': duration,
            'total_volume_kg': total_volume,
            'category': category,
            'estimated_calories_burned': calories
        }, status=status.HTTP_200_OK)


