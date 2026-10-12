"""
Progress analytics and body composition trends services.
"""

from .models import BodyMeasurement

def calculate_body_composition_trends(user, height_cm=175.0):
    """
    Analyzes historical body measurements to produce trends, rate of weight change, and BMI.
    """
    measurements = list(BodyMeasurement.objects.filter(user=user).order_by('date'))
    height_m = max(1.0, float(height_cm) / 100.0)

    if not measurements:
        profile = getattr(user, 'profile', None)
        curr_w = profile.current_weight_kg if (profile and profile.current_weight_kg) else 75.0
        bmi = round(curr_w / (height_m ** 2), 1)
        return {
            'has_data': False,
            'current_weight_kg': curr_w,
            'bmi': bmi,
            'bmi_category': _get_bmi_category(bmi),
            'total_weight_delta_kg': 0.0,
            'body_fat_delta_percent': 0.0,
            'measurements_count': 0,
            'history': [],
        }

    first = measurements[0]
    latest = measurements[-1]

    weight_delta = round(latest.weight_kg - first.weight_kg, 1)

    bf_delta = 0.0
    if latest.body_fat_percent is not None and first.body_fat_percent is not None:
        bf_delta = round(latest.body_fat_percent - first.body_fat_percent, 1)

    days = max(1, (latest.date - first.date).days)
    weeks = days / 7.0
    rate_kg_per_week = round(weight_delta / weeks, 2) if weeks >= 1.0 else 0.0

    current_bmi = round(latest.weight_kg / (height_m ** 2), 1)

    history = [
        {
            'date': m.date.isoformat(),
            'weight_kg': m.weight_kg,
            'body_fat_percent': m.body_fat_percent,
            'bmi': round(m.weight_kg / (height_m ** 2), 1),
        }
        for m in measurements
    ]

    return {
        'has_data': True,
        'current_weight_kg': latest.weight_kg,
        'starting_weight_kg': first.weight_kg,
        'total_weight_delta_kg': weight_delta,
        'weekly_rate_kg': rate_kg_per_week,
        'current_body_fat_percent': latest.body_fat_percent,
        'body_fat_delta_percent': bf_delta,
        'current_bmi': current_bmi,
        'bmi_category': _get_bmi_category(current_bmi),
        'measurements_count': len(measurements),
        'history': history,
    }


def _get_bmi_category(bmi):
    if bmi < 18.5:
        return 'Underweight'
    elif bmi < 25.0:
        return 'Normal'
    elif bmi < 30.0:
        return 'Overweight'
    return 'Obese'
