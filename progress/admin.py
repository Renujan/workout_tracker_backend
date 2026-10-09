from django.contrib import admin
from .models import BodyMeasurement, ProgressPhoto, FitnessGoal, Achievement, FitnessInsight


@admin.register(BodyMeasurement)
class BodyMeasurementAdmin(admin.ModelAdmin):
    list_display = ['user', 'date', 'weight_kg', 'body_fat_percent']
    date_hierarchy = 'date'


@admin.register(ProgressPhoto)
class ProgressPhotoAdmin(admin.ModelAdmin):
    list_display = ['user', 'date', 'category', 'weight_kg']
    list_filter = ['category']


@admin.register(FitnessGoal)
class FitnessGoalAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'category', 'current_value', 'target_value', 'deadline', 'is_completed']
    list_filter = ['category', 'is_completed']


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'category', 'unlocked', 'unlocked_at']
    list_filter = ['unlocked', 'category']


@admin.register(FitnessInsight)
class FitnessInsightAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'type', 'date']
    list_filter = ['type']
    date_hierarchy = 'date'
