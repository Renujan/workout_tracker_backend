from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    WorkoutPlanViewSet, WorkoutSessionViewSet,
    WorkoutSetViewSet, CompletedWorkoutViewSet,
    OneRepMaxCalculatorView, CalorieEstimateView,
    WeeklySummaryView, WorkoutHistoryExportView,
    RestTimerCalculatorView, WorkoutActivityCalendarView,
    VolumeProgressionView
)

router = DefaultRouter()
router.register(r'plans', WorkoutPlanViewSet, basename='workout-plan')
router.register(r'sessions', WorkoutSessionViewSet, basename='workout-session')
router.register(r'sets', WorkoutSetViewSet, basename='workout-set')
router.register(r'history', CompletedWorkoutViewSet, basename='completed-workout')

urlpatterns = [
    path('calculator/1rm/', OneRepMaxCalculatorView.as_view(), name='workouts-calculator-1rm'),
    path('calculator/calories/', CalorieEstimateView.as_view(), name='workouts-calculator-calories'),
    path('calculator/rest-timer/', RestTimerCalculatorView.as_view(), name='workouts-calculator-rest-timer'),
    path('analytics/weekly-summary/', WeeklySummaryView.as_view(), name='workouts-weekly-summary'),
    path('analytics/activity-calendar/', WorkoutActivityCalendarView.as_view(), name='workouts-activity-calendar'),
    path('analytics/volume-progression/', VolumeProgressionView.as_view(), name='workouts-volume-progression'),
    path('history/export/', WorkoutHistoryExportView.as_view(), name='workouts-history-export'),
    path('', include(router.urls)),
]




