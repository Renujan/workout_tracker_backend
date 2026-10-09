from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MealItemViewSet, DailyNutritionViewSet

router = DefaultRouter()
router.register(r'meals', MealItemViewSet, basename='meal-item')
router.register(r'daily', DailyNutritionViewSet, basename='daily-nutrition')

urlpatterns = [
    path('', include(router.urls)),
]
