from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ExerciseViewSet, ExerciseHistoryViewSet, PersonalRecordViewSet

router = DefaultRouter()
router.register(r'', ExerciseViewSet, basename='exercise')
router.register(r'history', ExerciseHistoryViewSet, basename='exercise-history')
router.register(r'records', PersonalRecordViewSet, basename='personal-record')

urlpatterns = [
    path('', include(router.urls)),
]
