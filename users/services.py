"""
User preferences, unit conversion, and profile utility services.
"""
from typing import Dict, Any


class UserPreferencesService:
    """Service to handle user app preferences, units, and notifications."""

    DEFAULT_PREFERENCES: Dict[str, Any] = {
        'unit_system': 'metric',  # 'metric' (kg, km) or 'imperial' (lbs, miles)
        'weight_unit': 'kg',
        'distance_unit': 'km',
        'week_start_day': 'monday',
        'rest_timer_sound': True,
        'rest_timer_vibration': True,
        'auto_start_next_set': False,
        'theme': 'dark',
        'notifications': {
            'workout_reminder': True,
            'streak_saver': True,
            'hydration_alert': True,
            'weekly_summary': True,
        }
    }

    @classmethod
    def get_user_preferences(cls, user) -> Dict[str, Any]:
        """Fetch preferences merged with user profile settings."""
        prefs = dict(cls.DEFAULT_PREFERENCES)
        from .models import UserProfile
        profile = UserProfile.objects.filter(user=user).first()
        if profile:
            prefs['target_weekly_workouts'] = profile.weekly_workouts_target
            prefs['current_weight_kg'] = profile.current_weight_kg
            prefs['target_weight_kg'] = profile.target_weight_kg
        else:
            prefs['target_weekly_workouts'] = 4
            prefs['current_weight_kg'] = None
            prefs['target_weight_kg'] = None
        return prefs

    @staticmethod
    def convert_weight(value: float, from_unit: str = 'kg', to_unit: str = 'lbs') -> float:
        """Convert weight between kg and lbs (rounded to 2 decimal places)."""
        if from_unit == to_unit:
            return round(value, 2)
        if from_unit == 'kg' and to_unit == 'lbs':
            return round(value * 2.20462, 2)
        if from_unit == 'lbs' and to_unit == 'kg':
            return round(value / 2.20462, 2)
        raise ValueError(f"Unsupported weight units: {from_unit} -> {to_unit}")

    @staticmethod
    def convert_distance(value: float, from_unit: str = 'km', to_unit: str = 'miles') -> float:
        """Convert distance between kilometers and miles."""
        if from_unit == to_unit:
            return round(value, 2)
        if from_unit == 'km' and to_unit == 'miles':
            return round(value * 0.621371, 2)
        if from_unit == 'miles' and to_unit == 'km':
            return round(value / 0.621371, 2)
        raise ValueError(f"Unsupported distance units: {from_unit} -> {to_unit}")
