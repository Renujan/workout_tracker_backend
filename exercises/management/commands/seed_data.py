"""
Seed command: python manage.py seed_data

Creates a demo user 'renujan' and seeds all 5 apps with realistic data.
Safe to run multiple times — uses get_or_create throughout.
"""

import datetime
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone

from exercises.models import Exercise, ExerciseHistory, PersonalRecord
from users.models import UserProfile
from workouts.models import WorkoutPlan, PlanExercise, CompletedWorkout
from nutrition.models import MealItem, DailyNutrition
from progress.models import BodyMeasurement, FitnessGoal, Achievement, FitnessInsight


EXERCISES = [
    ('Bench Press', 'Chest', 'Barbell', 'Intermediate', 'Compound push movement targeting the pectorals.'),
    ('Squat', 'Legs', 'Barbell', 'Intermediate', 'King of lower-body movements.'),
    ('Deadlift', 'Back', 'Barbell', 'Advanced', 'Full-body pull; targets posterior chain.'),
    ('Overhead Press', 'Shoulders', 'Barbell', 'Intermediate', 'Strict vertical press for shoulder mass.'),
    ('Barbell Row', 'Back', 'Barbell', 'Intermediate', 'Horizontal pull for back thickness.'),
    ('Pull Up', 'Back', 'Bodyweight', 'Intermediate', 'Vertical pull; great lat width builder.'),
    ('Dumbbell Curl', 'Biceps', 'Dumbbell', 'Beginner', 'Isolation curl for bicep peak.'),
    ('Tricep Pushdown', 'Triceps', 'Cable', 'Beginner', 'Cable isolation for tricep development.'),
    ('Leg Press', 'Legs', 'Machine', 'Beginner', 'Machine quad-dominant pressing movement.'),
    ('Romanian Deadlift', 'Legs', 'Barbell', 'Intermediate', 'Hip-hinge targeting hamstrings and glutes.'),
    ('Incline Dumbbell Press', 'Chest', 'Dumbbell', 'Intermediate', 'Upper-chest focused press.'),
    ('Lateral Raise', 'Shoulders', 'Dumbbell', 'Beginner', 'Isolation for medial deltoid.'),
    ('Cable Fly', 'Chest', 'Cable', 'Beginner', 'Constant-tension chest isolation.'),
    ('Face Pull', 'Shoulders', 'Cable', 'Beginner', 'Rear delt and rotator cuff health.'),
    ('Plank', 'Abs', 'Bodyweight', 'Beginner', 'Isometric core stability.'),
]


class Command(BaseCommand):
    help = 'Seed database with demo data for ProgressX (user: renujan / pass: gym12345)'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('[SEED] Seeding database...'))
        today = datetime.date.today()

        # ── 1. User ────────────────────────────────────────────────────────────
        user, created = User.objects.get_or_create(
            username='renujan',
            defaults={'email': 'renujan@progressx.app', 'first_name': 'Renujan', 'last_name': ''},
        )
        if created:
            user.set_password('gym12345')
            user.save()
        self.stdout.write(f'  {"Created" if created else "Exists"} user: renujan')

        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.current_streak = 12
        profile.longest_streak = 21
        profile.weekly_workouts_target = 5
        profile.weekly_workouts_completed = 4
        profile.weekly_completion = 87.0
        profile.current_weight_kg = 78.5
        profile.target_weight_kg = 80.0
        profile.training_since = datetime.date(2024, 1, 15)
        profile.total_workouts = 147
        profile.total_volume_kg = 128450
        profile.total_sets = 1840
        profile.total_prs = 23
        profile.save()

        # ── 2. Exercises ───────────────────────────────────────────────────────
        ex_objs = {}
        for name, muscle, equip, diff, desc in EXERCISES:
            ex, _ = Exercise.objects.get_or_create(
                name=name,
                defaults={'muscle_group': muscle, 'equipment': equip, 'difficulty': diff, 'description': desc},
            )
            ex_objs[name] = ex
        self.stdout.write(f'  Seeded {len(ex_objs)} exercises')

        # ── 3. Exercise history (bench press 8 weeks) ─────────────────────────
        bench = ex_objs['Bench Press']
        bench_data = [
            (today - datetime.timedelta(weeks=8), 80, 8),
            (today - datetime.timedelta(weeks=7), 82.5, 7),
            (today - datetime.timedelta(weeks=6), 85, 6),
            (today - datetime.timedelta(weeks=5), 85, 8),
            (today - datetime.timedelta(weeks=4), 87.5, 6),
            (today - datetime.timedelta(weeks=3), 90, 5),
            (today - datetime.timedelta(weeks=2), 92.5, 5),
            (today - datetime.timedelta(weeks=1), 95, 4),
        ]
        for date, weight, reps in bench_data:
            ExerciseHistory.objects.update_or_create(
                user=user, exercise=bench, date=date,
                defaults={'weight_kg': weight, 'reps': reps},
            )
        self.stdout.write(f'  Seeded bench press history (8 pts)')

        # ── 4. Personal record ─────────────────────────────────────────────────
        PersonalRecord.objects.update_or_create(
            user=user, exercise=bench,
            defaults={
                'weight_kg': 100, 'reps': 3,
                'previous_weight_kg': 95, 'previous_reps': 4,
                'improvement_kg': 5, 'date': today - datetime.timedelta(days=3),
                'category': 'strength',
            },
        )

        # ── 5. Workout plan ────────────────────────────────────────────────────
        plan, _ = WorkoutPlan.objects.get_or_create(
            user=user, name='Push Day A',
            defaults={'category': 'Push', 'estimated_minutes': 65},
        )
        push_exercises = [
            (ex_objs['Bench Press'], 0, 4, '6-8', 90),
            (ex_objs['Overhead Press'], 1, 4, '8-10', 55),
            (ex_objs['Incline Dumbbell Press'], 2, 3, '10-12', 30),
            (ex_objs['Lateral Raise'], 3, 3, '12-15', 12),
            (ex_objs['Tricep Pushdown'], 4, 3, '12-15', 35),
        ]
        for exercise, order, sets, reps, weight in push_exercises:
            PlanExercise.objects.update_or_create(
                plan=plan, exercise=exercise,
                defaults={'order': order, 'target_sets': sets, 'target_reps': reps, 'target_weight_kg': weight},
            )

        # ── 6. Completed workouts (last 2 weeks) ───────────────────────────────
        cw_data = [
            ('Push Day A', 'Push', 65, 4820, 20, -1),
            ('Pull Day B', 'Pull', 72, 5100, 22, -3),
            ('Legs Day C', 'Legs', 80, 6200, 24, -5),
            ('Push Day A', 'Push', 68, 5000, 20, -7),
            ('Pull Day B', 'Pull', 70, 4950, 22, -9),
        ]
        for name, cat, dur, vol, sets, day_offset in cw_data:
            CompletedWorkout.objects.update_or_create(
                user=user, name=name,
                date=today + datetime.timedelta(days=day_offset),
                defaults={'category': cat, 'duration_minutes': dur, 'total_volume_kg': vol, 'total_sets': sets},
            )
        self.stdout.write(f'  Seeded 5 completed workouts')

        # ── 7. Daily nutrition (today) ─────────────────────────────────────────
        dn, _ = DailyNutrition.objects.update_or_create(
            user=user, date=today,
            defaults={
                'calories': 2150, 'target_calories': 2500,
                'protein_grams': 112, 'target_protein_grams': 150,
                'carbs_grams': 230, 'target_carbs_grams': 300,
                'fat_grams': 60, 'target_fat_grams': 80,
                'water_liters': 2.5, 'target_water_liters': 3.0,
            },
        )
        meals = [
            ('Breakfast', 'Oats + Protein Shake', 520, 42, 65, 8, '1 serving'),
            ('Lunch', 'Grilled Chicken & Rice', 680, 52, 78, 12, '400g'),
            ('Snack', 'Greek Yogurt', 180, 18, 20, 3, '200g'),
            ('Dinner', 'Salmon & Vegetables', 640, 45, 35, 28, '350g'),
        ]
        for cat, name, cal, prot, carb, fat, serving in meals:
            MealItem.objects.update_or_create(
                user=user, date=today, name=name,
                defaults={'category': cat, 'calories': cal, 'protein_grams': prot,
                          'carbs_grams': carb, 'fat_grams': fat, 'serving_size': serving},
            )
        self.stdout.write(f'  Seeded daily nutrition + 4 meals')

        # ── 8. Body measurements ───────────────────────────────────────────────
        measurements = [
            (today - datetime.timedelta(weeks=8), 82.0, 18.5, 100, 38, 84, 58),
            (today - datetime.timedelta(weeks=4), 80.2, 17.2, 101, 39, 82, 59),
            (today, 78.5, 16.1, 102, 40, 80, 60),
        ]
        for date, weight, fat, chest, arms, waist, thighs in measurements:
            BodyMeasurement.objects.update_or_create(
                user=user, date=date,
                defaults={
                    'weight_kg': weight, 'body_fat_percent': fat,
                    'chest_cm': chest, 'arms_cm': arms, 'waist_cm': waist, 'thighs_cm': thighs,
                },
            )
        self.stdout.write(f'  Seeded 3 body measurements')

        # ── 9. Goals ───────────────────────────────────────────────────────────
        goals = [
            ('Bench 100kg 1RM', 'exercise', 100, 95, 'kg', today + datetime.timedelta(days=30)),
            ('Reach 80kg Body Weight', 'weight', 80, 78.5, 'kg', today + datetime.timedelta(days=60)),
            ('Hit Protein Target 30 Days', 'nutrition', 30, 18, 'days', today + datetime.timedelta(days=30)),
        ]
        for title, cat, target, current, unit, deadline in goals:
            FitnessGoal.objects.update_or_create(
                user=user, title=title,
                defaults={'category': cat, 'target_value': target, 'current_value': current,
                          'unit': unit, 'deadline': deadline},
            )

        # ── 10. Achievements ────────────────────────────────────────────────────
        achievements = [
            ('First Workout', 'Log your first workout session', 'milestone', 'Dumbbell', True, 1, 1),
            ('10 Workouts', 'Complete 10 workout sessions', 'milestone', 'Trophy', True, 10, 10),
            ('Protein Streak — 7 Days', 'Hit protein target 7 days in a row', 'nutrition', 'Flame', True, 7, 7),
            ('Century Club', 'Lift 100kg+ on any compound', 'strength', 'Zap', False, 95, 100),
            ('Iron Will — 30 Days', 'Maintain a 30-day streak', 'consistency', 'Shield', False, 12, 30),
        ]
        for title, desc, cat, icon, unlocked, prog, max_prog in achievements:
            Achievement.objects.update_or_create(
                user=user, title=title,
                defaults={
                    'description': desc, 'category': cat, 'icon_name': icon,
                    'unlocked': unlocked, 'progress': prog, 'max_progress': max_prog,
                    'unlocked_at': timezone.make_aware(datetime.datetime(2026, 9, 1, 12, 0)) if unlocked else None,
                },
            )

        # ── 11. Insights ────────────────────────────────────────────────────────
        insights = [
            ('strength', 'Progressive Overload On Track', 'Bench +15kg in 8 weeks', 'Your bench press has grown by 15kg over 8 weeks — keep the progressive overload going.', 'Trending Up'),
            ('nutrition', 'Protein Consistency Improving', 'Hit protein target 18/30 days', 'You hit your protein target 18 out of the last 30 days. Aim for 25+ to maximize muscle retention.', 'Needs Focus'),
            ('volume', 'Weekly Volume Up 12%', 'Total volume increased 12% vs last month', 'Your total training volume increased by 12% compared to last month — great sign of progression.', 'Positive'),
        ]
        for itype, title, summary, detail, tag in insights:
            FitnessInsight.objects.update_or_create(
                user=user, title=title,
                defaults={'type': itype, 'summary': summary, 'detail': detail, 'tag': tag, 'date': today},
            )

        self.stdout.write(self.style.SUCCESS(
            '\n[DONE] Seed complete!\n'
            '   Login: renujan / gym12345\n'
            '   Run: python manage.py runserver\n'
        ))
