
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

    lessons_count = serializers.SerializerMethodField()
    lessons = LessonSerializer(many=True, read_only=True)

    class Meta:
        model = Course
        fields = '__all__'  # Включаем все поля модели

    def get_lessons_count(self, obj):
        """
        Метод для SerializerMethodField.
        Возвращает количество уроков для конкретного курса.
        """
        return obj.lessons.count()
