from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status, generics
from rest_framework.response import Response
from materials.models import Course, Lesson
from materials.serializers import CourseSerializer, LessonSerializer


# ViewSet для курса (полный CRUD)
class CourseViewSet(viewsets.ViewSet):
    """
    ViewSet для работы с курсами:
    - list: получение списка курсов
    - retrieve: получение одного курса
    - create: создание курса
    - update: полное обновление курса
    - partial_update: частичное обновление курса
    - destroy: удаление курса
    """

    def list(self, request):
        """Получение списка всех курсов"""
        queryset = Course.objects.all()
        serializer = CourseSerializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        """Получение одного курса по ID"""
        queryset = Course.objects.all()
        course = get_object_or_404(queryset, pk=pk)
        serializer = CourseSerializer(course)
        return Response(serializer.data)

    def create(self, request):
        """Создание нового курса"""
        serializer = CourseSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk=None):
        """Полное обновление курса"""
        queryset = Course.objects.all()
        course = get_object_or_404(queryset, pk=pk)
        serializer = CourseSerializer(course, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def partial_update(self, request, pk=None):
        """Частичное обновление курса"""
        queryset = Course.objects.all()
        course = get_object_or_404(queryset, pk=pk)
        serializer = CourseSerializer(course, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None):
        """Удаление курса"""
        queryset = Course.objects.all()
        course = get_object_or_404(queryset, pk=pk)
        course.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# Generic-классы для урока
class LessonListCreateView(generics.ListCreateAPIView):
    """
    Generic-класс для:
    - получения списка уроков (GET)
    - создания нового урока (POST)
    """
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer


class LessonRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """
    Generic-класс для:
    - получения одного урока (GET)
    - обновления урока (PUT/PATCH)
    - удаления урока (DELETE)
    """
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer

