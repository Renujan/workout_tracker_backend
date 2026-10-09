from django.contrib import admin
from .models import MealItem, DailyNutrition


@admin.register(MealItem)
class MealItemAdmin(admin.ModelAdmin):
    list_display = ['user', 'name', 'category', 'date', 'calories', 'protein_grams']
    list_filter = ['category', 'date']
    search_fields = ['name']
    date_hierarchy = 'date'


@admin.register(DailyNutrition)
class DailyNutritionAdmin(admin.ModelAdmin):
    list_display = ['user', 'date', 'calories', 'protein_grams', 'water_liters']
    date_hierarchy = 'date'
