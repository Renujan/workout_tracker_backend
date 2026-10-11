from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend

from .models import WorkoutPlan, WorkoutSession, CompletedWorkout, WorkoutSet
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
