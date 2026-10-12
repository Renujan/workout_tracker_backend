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

