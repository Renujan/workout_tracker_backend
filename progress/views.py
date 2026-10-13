from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend


from .models import BodyMeasurement, ProgressPhoto, FitnessGoal, Achievement, FitnessInsight
from .serializers import (
    BodyMeasurementSerializer, ProgressPhotoSerializer,
    FitnessGoalSerializer, AchievementSerializer, FitnessInsightSerializer,
)


class BodyMeasurementViewSet(viewsets.ModelViewSet):
    serializer_class = BodyMeasurementSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['date']
    ordering_fields = ['date', 'weight_kg']

    def get_queryset(self):
        return BodyMeasurement.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ProgressPhotoViewSet(viewsets.ModelViewSet):
    serializer_class = ProgressPhotoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['category']
    ordering_fields = ['date']

    def get_queryset(self):
        return ProgressPhoto.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class FitnessGoalViewSet(viewsets.ModelViewSet):
    serializer_class = FitnessGoalSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['category', 'is_completed']
    ordering_fields = ['deadline', 'created_at']

    def get_queryset(self):
        return FitnessGoal.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['post'])
    def evaluate(self, request):
        """POST /api/v1/progress/goals/evaluate/ — evaluate goal progression and mark completed."""
        from .services import evaluate_fitness_goals
        count = evaluate_fitness_goals(request.user)
        goals = self.get_queryset()
        serializer = self.get_serializer(goals, many=True)
        return Response({
            'evaluated_count': count,
            'goals': serializer.data
        }, status=status.HTTP_200_OK)



class AchievementViewSet(viewsets.ModelViewSet):
    serializer_class = AchievementSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['unlocked', 'category']

    def get_queryset(self):
        return Achievement.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['post'])
    def sync(self, request):
        """POST /api/v1/progress/achievements/sync/ — evaluate and unlock milestones."""
        from .services import evaluate_and_sync_achievements
        result = evaluate_and_sync_achievements(request.user)
        achievements = self.get_queryset()
        serializer = self.get_serializer(achievements, many=True)
        return Response({
            'sync_summary': result,
            'achievements': serializer.data,
        }, status=status.HTTP_200_OK)


class FitnessInsightViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = FitnessInsightSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['type']
    ordering_fields = ['date']

    def get_queryset(self):
        return FitnessInsight.objects.filter(user=self.request.user)


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .services import calculate_body_composition_trends, calculate_circumference_deltas


class BodyCompositionTrendsView(APIView):
    """GET /api/v1/progress/analytics/trends/ — body composition trends, BMI, and weight delta."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        height = request.query_params.get('height_cm', 175.0)
        try:
            height = float(height)
        except (ValueError, TypeError):
            height = 175.0

        trends = calculate_body_composition_trends(request.user, height_cm=height)
        return Response(trends, status=status.HTTP_200_OK)


class BodyCircumferenceDeltasView(APIView):
    """GET /api/v1/progress/analytics/circumference/ — track body circumference measurements and deltas."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = calculate_circumference_deltas(request.user)
        return Response(data, status=status.HTTP_200_OK)

