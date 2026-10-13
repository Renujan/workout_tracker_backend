from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend

from .models import MealItem, DailyNutrition
from .serializers import MealItemSerializer, DailyNutritionSerializer


class MealItemViewSet(viewsets.ModelViewSet):
    """CRUD for individual meal log entries, scoped to requesting user."""
    serializer_class = MealItemSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['date', 'category']
    search_fields = ['name']
    ordering_fields = ['date', 'calories', 'protein_grams']

    def get_queryset(self):
        return MealItem.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class DailyNutritionViewSet(viewsets.ModelViewSet):
    """CRUD for daily nutrition snapshots (one record per day per user)."""
    serializer_class = DailyNutritionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['date']
    ordering_fields = ['date']

    def get_queryset(self):
        return DailyNutrition.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .services import calculate_tdee_and_macros


class MacroRecommendationView(APIView):
    """POST /api/v1/nutrition/recommendations/ — calculate BMR, TDEE, and recommended macros."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        profile = getattr(request.user, 'profile', None)
        default_weight = profile.current_weight_kg if (profile and profile.current_weight_kg) else 75.0

        weight = request.data.get('weight_kg', default_weight)
        height = request.data.get('height_cm', 175.0)
        age = request.data.get('age', 25)
        gender = request.data.get('gender', 'male')
        activity = request.data.get('activity_level', 'moderate')
        goal = request.data.get('goal', 'maintain')

        try:
            result = calculate_tdee_and_macros(
                weight_kg=weight,
                height_cm=height,
                age=age,
                gender=gender,
                activity_level=activity,
                goal=goal
            )
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


from django.utils import timezone
import datetime
from .services import get_daily_macro_summary


class DailyMacroSummaryView(APIView):
    """GET /api/v1/nutrition/summary/daily/?date=YYYY-MM-DD — get daily consumed macros vs target."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        date_str = request.query_params.get('date')
        if date_str:
            try:
                query_date = datetime.date.fromisoformat(date_str)
            except ValueError:
                return Response({'error': 'Invalid date format. Use YYYY-MM-DD.'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            query_date = timezone.now().date()

        summary = get_daily_macro_summary(request.user, query_date)
        return Response(summary, status=status.HTTP_200_OK)


from .services import calculate_hydration_target, get_or_update_hydration


class HydrationTrackerView(APIView):
    """GET/POST /api/v1/nutrition/hydration/ — water tracking and dynamic hydration targets."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        date_str = request.query_params.get('date')
        if date_str:
            try:
                query_date = datetime.date.fromisoformat(date_str)
            except ValueError:
                return Response({'error': 'Invalid date format. Use YYYY-MM-DD.'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            query_date = timezone.now().date()

        profile = getattr(request.user, 'profile', None)
        weight = profile.current_weight_kg if (profile and profile.current_weight_kg) else 75.0
        recommendation = calculate_hydration_target(weight_kg=weight)
        current_data = get_or_update_hydration(request.user, query_date)
        return Response({
            'status': current_data,
            'recommendation': recommendation,
        }, status=status.HTTP_200_OK)

    def post(self, request):
        date_str = request.data.get('date')
        if date_str:
            try:
                query_date = datetime.date.fromisoformat(date_str)
            except ValueError:
                return Response({'error': 'Invalid date format.'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            query_date = timezone.now().date()

        add_liters = request.data.get('add_liters')
        set_liters = request.data.get('set_liters')
        current_data = get_or_update_hydration(
            request.user, query_date, add_liters=add_liters, set_liters=set_liters
        )
        return Response(current_data, status=status.HTTP_200_OK)


from .services import calculate_nutrient_timing


class NutrientTimingRecommendationView(APIView):
    """GET/POST /api/v1/nutrition/recommendations/timing/ — pre and post workout nutrition timing guidelines."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = getattr(request.user, 'profile', None)
        weight = profile.current_weight_kg if (profile and profile.current_weight_kg) else 75.0
        intensity = request.query_params.get('intensity', 'moderate')
        duration = request.query_params.get('duration_minutes', 60)
        data = calculate_nutrient_timing(
            weight_kg=weight,
            workout_intensity=intensity,
            workout_duration_minutes=duration
        )
        return Response(data, status=status.HTTP_200_OK)

    def post(self, request):
        profile = getattr(request.user, 'profile', None)
        default_weight = profile.current_weight_kg if (profile and profile.current_weight_kg) else 75.0
        weight = request.data.get('weight_kg', default_weight)
        intensity = request.data.get('intensity', 'moderate')
        duration = request.data.get('duration_minutes', 60)
        data = calculate_nutrient_timing(
            weight_kg=weight,
            workout_intensity=intensity,
            workout_duration_minutes=duration
        )
        return Response(data, status=status.HTTP_200_OK)


