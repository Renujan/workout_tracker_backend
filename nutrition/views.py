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
