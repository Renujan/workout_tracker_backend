from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    BodyMeasurementViewSet, ProgressPhotoViewSet,
    FitnessGoalViewSet, AchievementViewSet, FitnessInsightViewSet,
    BodyCompositionTrendsView
)

router = DefaultRouter()
router.register(r'measurements', BodyMeasurementViewSet, basename='body-measurement')
router.register(r'photos', ProgressPhotoViewSet, basename='progress-photo')
router.register(r'goals', FitnessGoalViewSet, basename='fitness-goal')
router.register(r'achievements', AchievementViewSet, basename='achievement')
router.register(r'insights', FitnessInsightViewSet, basename='fitness-insight')

urlpatterns = [
    path('analytics/trends/', BodyCompositionTrendsView.as_view(), name='progress-analytics-trends'),
    path('', include(router.urls)),
]

