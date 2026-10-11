from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    WorkoutPlanViewSet, WorkoutSessionViewSet,
    WorkoutSetViewSet, CompletedWorkoutViewSet
)

router = DefaultRouter()
router.register(r'plans', WorkoutPlanViewSet, basename='workout-plan')
router.register(r'sessions', WorkoutSessionViewSet, basename='workout-session')
router.register(r'sets', WorkoutSetViewSet, basename='workout-set')
router.register(r'history', CompletedWorkoutViewSet, basename='completed-workout')

urlpatterns = [
    path('', include(router.urls)),
]
