from django.contrib import admin
from .models import Exercise, ExerciseHistory, PersonalRecord


@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ['name', 'muscle_group', 'equipment', 'difficulty']
    list_filter = ['muscle_group', 'equipment', 'difficulty']
    search_fields = ['name']


@admin.register(ExerciseHistory)
class ExerciseHistoryAdmin(admin.ModelAdmin):
    list_display = ['user', 'exercise', 'date', 'weight_kg', 'reps', 'estimated_1rm']
    list_filter = ['exercise__muscle_group']


@admin.register(PersonalRecord)
class PersonalRecordAdmin(admin.ModelAdmin):
    list_display = ['user', 'exercise', 'weight_kg', 'reps', 'date', 'category']
    list_filter = ['category']
