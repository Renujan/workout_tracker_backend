from django.urls import path
from .views import ProfileView, UserPreferencesView

urlpatterns = [
    path('profile/', ProfileView.as_view(), name='user-profile'),
    path('preferences/', UserPreferencesView.as_view(), name='user-preferences'),
]
