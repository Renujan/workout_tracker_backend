from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MealItemViewSet, DailyNutritionViewSet, MacroRecommendationView

router = DefaultRouter()
router.register(r'meals', MealItemViewSet, basename='meal-item')
router.register(r'daily', DailyNutritionViewSet, basename='daily-nutrition')

urlpatterns = [
    path('recommendations/', MacroRecommendationView.as_view(), name='nutrition-recommendations'),
    path('', include(router.urls)),
]

