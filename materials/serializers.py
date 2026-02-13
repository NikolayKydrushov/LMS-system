
from rest_framework import serializers
from materials.models import Course, Lesson

class LessonSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели урока
    """
    class Meta:
        model = Lesson
        fields = '__all__'  # Включаем все поля модели


class CourseSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели курса
    """

    lessons_count = serializers.IntegerField(source='lessons.count', read_only=True)
    lessons = LessonSerializer(many=True, read_only=True)

    class Meta:
        model = Course
        fields = '__all__'  # Включаем все поля модели
