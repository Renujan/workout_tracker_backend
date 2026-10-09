from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend

from .models import Exercise, ExerciseHistory, PersonalRecord
from .serializers import ExerciseSerializer, ExerciseHistorySerializer, PersonalRecordSerializer


class ExerciseViewSet(viewsets.ReadOnlyModelViewSet):
    """GET /api/v1/exercises/ — searchable, filterable exercise library (read-only)."""
    queryset = Exercise.objects.all()
    serializer_class = ExerciseSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['muscle_group', 'equipment', 'difficulty']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'muscle_group']


class ExerciseHistoryViewSet(viewsets.ModelViewSet):
    """CRUD for a user's per-exercise history points."""
    serializer_class = ExerciseHistorySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['exercise']
    ordering_fields = ['date']

    def get_queryset(self):
        return ExerciseHistory.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class PersonalRecordViewSet(viewsets.ModelViewSet):
    """CRUD for personal records, scoped to the requesting user."""
    serializer_class = PersonalRecordSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['exercise', 'category']
    ordering_fields = ['date', 'weight_kg']

    def get_queryset(self):
        return PersonalRecord.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
