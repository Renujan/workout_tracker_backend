"""
Nutrition calculation and recommendation services.
Includes Mifflin-St Jeor BMR, TDEE, and macronutrient targets.
"""

def calculate_tdee_and_macros(
    weight_kg,
    height_cm=175.0,
    age=25,
    gender='male',
    activity_level='moderate',
    goal='maintain'
):
    """
    Computes BMR, TDEE, and optimal macronutrient split based on physical stats and fitness goal.
    """
    w = float(weight_kg)
    h = float(height_cm)
    a = int(age)

    # Mifflin-St Jeor equation
    if gender.lower() == 'female':
        bmr = (10.0 * w) + (6.25 * h) - (5.0 * a) - 161.0
    else:
        bmr = (10.0 * w) + (6.25 * h) - (5.0 * a) + 5.0

    multipliers = {
        'sedentary': 1.2,
        'light': 1.375,
        'moderate': 1.55,
        'active': 1.725,
        'very_active': 1.9,
    }
    multiplier = multipliers.get(activity_level.lower(), 1.55)
    tdee = bmr * multiplier

    goal_adjustments = {
        'cut': -500.0,
        'aggressive_cut': -750.0,
        'lean_bulk': 300.0,
        'aggressive_bulk': 500.0,
        'maintain': 0.0,
    }
    target_cals = max(1200.0, tdee + goal_adjustments.get(goal.lower(), 0.0))

    # Macros: 2.0g/kg protein, 25% calories from fat, rest from carbs
    protein_g = round(w * 2.0, 1)
    protein_cals = protein_g * 4.0

    fat_cals = target_cals * 0.25
    fat_g = round(fat_cals / 9.0, 1)

    carb_cals = max(0.0, target_cals - protein_cals - fat_cals)
    carb_g = round(carb_cals / 4.0, 1)

    return {
        'bmr': round(bmr),
        'tdee': round(tdee),
        'target_calories': round(target_cals),
        'target_protein_g': protein_g,
        'target_carbs_g': carb_g,
        'target_fat_g': fat_g,
        'goal': goal,
        'activity_level': activity_level,
    }


def get_daily_macro_summary(user, query_date):
    """
    Computes consumed macros vs daily targets from logged MealItems and DailyNutrition.
    """
    from .models import MealItem, DailyNutrition
    meals = MealItem.objects.filter(user=user, date=query_date)

    consumed_cals = sum(m.calories for m in meals)
    consumed_protein = sum(m.protein_grams for m in meals)
    consumed_carbs = sum(m.carbs_grams for m in meals)
    consumed_fat = sum(m.fat_grams for m in meals)

    daily_record = DailyNutrition.objects.filter(user=user, date=query_date).first()
    target_cals = daily_record.target_calories if daily_record else 2400
    target_protein = daily_record.target_protein_grams if daily_record else 160
    target_carbs = daily_record.target_carbs_grams if daily_record else 250
    target_fat = daily_record.target_fat_grams if daily_record else 70

    remaining_cals = target_cals - consumed_cals
    protein_pct = round((consumed_protein / max(1, target_protein)) * 100, 1)

    return {
        'date': query_date.isoformat(),
        'meals_logged': meals.count(),
        'consumed': {
            'calories': consumed_cals,
            'protein_grams': round(consumed_protein, 1),
            'carbs_grams': round(consumed_carbs, 1),
            'fat_grams': round(consumed_fat, 1),
        },
        'targets': {
            'calories': target_cals,
            'protein_grams': target_protein,
            'carbs_grams': target_carbs,
            'fat_grams': target_fat,
        },
        'remaining_calories': remaining_cals,
        'protein_adherence_percentage': min(100.0, protein_pct),
        'is_calorie_deficit': consumed_cals < target_cals,
    }


def calculate_hydration_target(weight_kg=75.0, workout_minutes=0):
    """
    Calculates recommended daily water intake based on body weight and workout duration.
    Base: 35ml per kg of bodyweight.
    Exercise addition: +500ml per 45 minutes of training.
    """
    w = max(40.0, float(weight_kg))
    base_ml = w * 35.0
    extra_ml = (max(0, int(workout_minutes)) / 45.0) * 500.0
    total_ml = base_ml + extra_ml
    total_liters = round(total_ml / 1000.0, 2)
    glasses = round(total_ml / 250.0)

    return {
        'weight_kg': w,
        'workout_minutes': workout_minutes,
        'recommended_water_liters': total_liters,
        'recommended_water_ml': round(total_ml),
        'recommended_glasses_250ml': glasses,
        'base_liters': round(base_ml / 1000.0, 2),
        'exercise_liters': round(extra_ml / 1000.0, 2),
        'hydration_tip': 'Drink 500ml upon waking and hydrate evenly throughout your workout.',
    }


def get_or_update_hydration(user, query_date, add_liters=None, set_liters=None):
    """
    Fetches or updates daily water consumption for a user.
    """
    from .models import DailyNutrition
    daily, _ = DailyNutrition.objects.get_or_create(
        user=user, date=query_date,
        defaults={'target_water_liters': 3.0}
    )

    if set_liters is not None:
        daily.water_liters = max(0.0, round(float(set_liters), 2))
        daily.save(update_fields=['water_liters'])
    elif add_liters is not None:
        daily.water_liters = max(0.0, round(daily.water_liters + float(add_liters), 2))
        daily.save(update_fields=['water_liters'])

    target = daily.target_water_liters or 3.0
    completion_pct = round((daily.water_liters / max(0.1, target)) * 100.0, 1)

    return {
        'date': query_date.isoformat(),
        'water_liters': daily.water_liters,
        'target_water_liters': target,
        'completion_percentage': min(100.0, completion_pct),
        'glasses_drank': round(daily.water_liters * 4.0),
        'target_glasses': round(target * 4.0),
        'goal_met': daily.water_liters >= target,
    }


def calculate_nutrient_timing(weight_kg=75.0, workout_intensity='moderate', workout_duration_minutes=60):
    """
    Generates pre-workout fuel, intra-workout hydration, and post-workout recovery macro windows.
    Based on ISSN (International Society of Sports Nutrition) guidelines.
    """
    w = max(40.0, float(weight_kg))
    duration = max(15, int(workout_duration_minutes))

    # Pre-workout (60-90m before)
    pre_carbs = round(w * 0.8, 1)
    pre_protein = round(w * 0.35, 1)
    pre_water_ml = 500

    # Post-workout (within 45-60m after)
    intensity_multiplier = 1.2 if workout_intensity.lower() in ['high', 'intense'] else 1.0
    post_carbs = round(w * 1.0 * intensity_multiplier, 1)
    post_protein = round(max(25.0, w * 0.4), 1)

    intra_recommendation = {
        'needed': duration > 60 or workout_intensity.lower() in ['high', 'intense'],
        'carbs_g': 30 if duration > 60 else 0,
        'water_ml_per_hour': 600,
        'electrolytes': 'Recommended for sweat-heavy sessions exceeding 60 minutes.',
    }

    return {
        'weight_kg': w,
        'workout_duration_minutes': duration,
        'workout_intensity': workout_intensity,
        'pre_workout': {
            'timing_window': '60-90 minutes before workout',
            'carbs_grams': pre_carbs,
            'protein_grams': pre_protein,
            'fat_grams_limit': 10,
            'water_ml': pre_water_ml,
            'suggested_foods': ['Oatmeal with whey protein', 'Banana with rice cakes', 'Toast with sliced chicken breast'],
            'guideline': 'Focus on easy-to-digest carbs and low fat to prevent GI discomfort.',
        },
        'intra_workout': intra_recommendation,
        'post_workout': {
            'timing_window': 'Within 45-60 minutes post-session',
            'carbs_grams': post_carbs,
            'protein_grams': post_protein,
            'carb_to_protein_ratio': f"{round(post_carbs / max(1, post_protein), 1)}:1",
            'suggested_foods': ['Whey isolate with cream of rice', 'Chicken breast with white rice & veggies', 'Greek yogurt with berries & honey'],
            'guideline': 'Prioritize high glycemic carbs for glycogen restoration and 25-40g high-leucine protein.',
        }
    }

