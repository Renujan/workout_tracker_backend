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
        return CompletedWorkout.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
