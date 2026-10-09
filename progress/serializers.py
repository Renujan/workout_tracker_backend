from rest_framework import serializers
from .models import BodyMeasurement, ProgressPhoto, FitnessGoal, Achievement, FitnessInsight


class BodyMeasurementSerializer(serializers.ModelSerializer):
    class Meta:
        model = BodyMeasurement
        fields = ['id', 'date', 'weight_kg', 'body_fat_percent',
                  'chest_cm', 'arms_cm', 'waist_cm', 'thighs_cm']


class ProgressPhotoSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = ProgressPhoto
        fields = ['id', 'date', 'category', 'image', 'image_url', 'weight_kg']
        read_only_fields = ['image_url']

    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return None


class FitnessGoalSerializer(serializers.ModelSerializer):
    progress_percent = serializers.FloatField(read_only=True)

    class Meta:
        model = FitnessGoal
        fields = ['id', 'title', 'category', 'target_value', 'current_value',
                  'unit', 'deadline', 'is_completed', 'progress_percent',
                  'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


class AchievementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Achievement
        fields = ['id', 'title', 'description', 'category', 'icon_name',
                  'unlocked', 'unlocked_at', 'progress', 'max_progress']


class FitnessInsightSerializer(serializers.ModelSerializer):
    class Meta:
        model = FitnessInsight
        fields = ['id', 'type', 'title', 'summary', 'detail', 'tag', 'date']
