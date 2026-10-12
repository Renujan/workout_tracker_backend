from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    WorkoutPlanViewSet, WorkoutSessionViewSet,
    WorkoutSetViewSet, CompletedWorkoutViewSet,
    OneRepMaxCalculatorView, CalorieEstimateView,
    WeeklySummaryView, WorkoutHistoryExportView
)

router = DefaultRouter()
router.register(r'plans', WorkoutPlanViewSet, basename='workout-plan')
router.register(r'sessions', WorkoutSessionViewSet, basename='workout-session')
router.register(r'sets', WorkoutSetViewSet, basename='workout-set')
router.register(r'history', CompletedWorkoutViewSet, basename='completed-workout')

urlpatterns = [
    path('calculator/1rm/', OneRepMaxCalculatorView.as_view(), name='workouts-calculator-1rm'),
    path('calculator/calories/', CalorieEstimateView.as_view(), name='workouts-calculator-calories'),
    path('analytics/weekly-summary/', WeeklySummaryView.as_view(), name='workouts-weekly-summary'),
    path('history/export/', WorkoutHistoryExportView.as_view(), name='workouts-history-export'),
    path('', include(router.urls)),
]




