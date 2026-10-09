from rest_framework import serializers
from .models import MealItem, DailyNutrition


class MealItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = MealItem
        fields = ['id', 'date', 'category', 'name', 'calories',
                  'protein_grams', 'carbs_grams', 'fat_grams',
                  'serving_size', 'image_url', 'created_at']
        read_only_fields = ['created_at']


class DailyNutritionSerializer(serializers.ModelSerializer):
    meals = serializers.SerializerMethodField()
    protein_hit = serializers.SerializerMethodField()

    class Meta:
        model = DailyNutrition
        fields = [
            'id', 'date', 'calories', 'target_calories',
            'protein_grams', 'target_protein_grams',
            'carbs_grams', 'target_carbs_grams',
            'fat_grams', 'target_fat_grams',
            'water_liters', 'target_water_liters',
            'meals', 'protein_hit',
        ]

    def get_meals(self, obj):
        meals = obj.user.meal_items.filter(date=obj.date)
        return MealItemSerializer(meals, many=True).data

    def get_protein_hit(self, obj):
        return obj.protein_grams >= obj.target_protein_grams
