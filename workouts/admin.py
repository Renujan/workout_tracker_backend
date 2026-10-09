from django.contrib import admin
from .models import WorkoutPlan, PlanExercise, WorkoutSession, SessionExercise, WorkoutSet, CompletedWorkout


class PlanExerciseInline(admin.TabularInline):
    model = PlanExercise
    extra = 0


@admin.register(WorkoutPlan)
class WorkoutPlanAdmin(admin.ModelAdmin):
    list_display = ['user', 'name', 'category', 'is_active', 'created_at']
    inlines = [PlanExerciseInline]


class SessionExerciseInline(admin.TabularInline):
    model = SessionExercise
    extra = 0


@admin.register(WorkoutSession)
class WorkoutSessionAdmin(admin.ModelAdmin):
    list_display = ['user', 'name', 'started_at', 'is_completed']
    list_filter = ['is_completed']
    inlines = [SessionExerciseInline]


@admin.register(CompletedWorkout)
class CompletedWorkoutAdmin(admin.ModelAdmin):
    list_display = ['user', 'name', 'category', 'date', 'total_volume_kg', 'total_sets']
    list_filter = ['category']
    date_hierarchy = 'date'
