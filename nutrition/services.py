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
