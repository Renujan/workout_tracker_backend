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

