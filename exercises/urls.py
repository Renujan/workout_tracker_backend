from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ExerciseViewSet, ExerciseHistoryViewSet, PersonalRecordViewSet

router = DefaultRouter()
# Register sub-paths BEFORE the root '' to avoid '' capturing them
router.register(r'history', ExerciseHistoryViewSet, basename='exercise-history')
router.register(r'records', PersonalRecordViewSet, basename='personal-record')
router.register(r'', ExerciseViewSet, basename='exercise')

urlpatterns = [
    path('', include(router.urls)),
]
