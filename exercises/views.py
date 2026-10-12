from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count
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

    @action(detail=False, methods=['get'])
    def categories(self, request):
        """GET /api/v1/exercises/categories/ — return choice options for filter dropdowns."""
        return Response({
            'muscle_groups': [choice[0] for choice in Exercise.MUSCLE_GROUP_CHOICES],
            'equipment': [choice[0] for choice in Exercise.EQUIPMENT_CHOICES],
            'difficulty': [choice[0] for choice in Exercise.DIFFICULTY_CHOICES],
        })

    @action(detail=False, methods=['get'])
    def muscle_groups(self, request):
        """GET /api/v1/exercises/muscle_groups/ — return exercise counts grouped by muscle group."""
        counts = Exercise.objects.values('muscle_group').annotate(count=Count('id')).order_by('muscle_group')
        return Response(list(counts))

    @action(detail=True, methods=['get'])
    def history(self, request, pk=None):
        """GET /api/v1/exercises/{id}/history/ — return user's performance history for this exercise."""
        exercise = self.get_object()
        history_qs = ExerciseHistory.objects.filter(user=request.user, exercise=exercise).order_by('-date')
        serializer = ExerciseHistorySerializer(history_qs, many=True)
        return Response(serializer.data)



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
