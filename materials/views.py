from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status, generics
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from materials.models import Course, Lesson
from materials.serializers import CourseSerializer, LessonSerializer
from users.permissions import IsModerator, IsOwner


class CourseViewSet(viewsets.ViewSet):
    """
    ViewSet для работы с курсами:
    - list: получение списка курсов (модераторы видят все, обычные пользователи - только свои)
    - retrieve: получение одного курса (модераторы видят любой, обычные - только свой)
    - create: создание курса (только для не-модераторов)
    - update: обновление курса (модераторы могут любые, обычные - только свои)
    - partial_update: частичное обновление (модераторы могут любые, обычные - только свои)
    - destroy: удаление курса (модераторам запрещено, обычные - только свои)
    """

    def get_permissions(self):
        """
        Определяем права доступа для разных действий
        """
        if self.action in ['list', 'retrieve']:
            permission_classes = [IsAuthenticated]
        elif self.action in ['create']:
            # Создание курса запрещено модераторам
            permission_classes = [IsAuthenticated, ~IsModerator]
        elif self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAuthenticated]

        return [permission() for permission in permission_classes]

    def list(self, request):
        """Получение списка всех курсов"""
        if IsModerator().has_permission(request, self):
            # Модераторы видят все курсы
            queryset = Course.objects.all()
        else:
            # Обычные пользователи видят только свои курсы
            queryset = Course.objects.filter(owner=request.user)

        serializer = CourseSerializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        """Получение одного курса по ID"""
        queryset = Course.objects.all()
        course = get_object_or_404(queryset, pk=pk)

        # Проверка прав доступа к объекту
        if not (IsModerator().has_permission(request, self) or course.owner == request.user):
            raise PermissionDenied("У вас нет прав для просмотра этого курса")

        serializer = CourseSerializer(course)
        return Response(serializer.data)

    def create(self, request):
        """Создание нового курса (только для не-модераторов)"""
        serializer = CourseSerializer(data=request.data)
        if serializer.is_valid():
            # Автоматически привязываем создателя к курсу
            serializer.save(owner=self.request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk=None):
        """Полное обновление курса"""
        course = self.get_object(pk)

        # Проверка прав доступа к объекту
        if not (IsModerator().has_permission(request, self) or course.owner == request.user):
            raise PermissionDenied("У вас нет прав для редактирования этого курса")

        serializer = CourseSerializer(course, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def partial_update(self, request, pk=None):
        """Частичное обновление курса"""
        course = self.get_object(pk)

        # Проверка прав доступа к объекту
        if not (IsModerator().has_permission(request, self) or course.owner == request.user):
            raise PermissionDenied("У вас нет прав для редактирования этого курса")

        serializer = CourseSerializer(course, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None):
        """Удаление курса"""
        course = self.get_object(pk)

        # Проверка прав доступа к объекту
        if IsModerator().has_permission(request, self):
            raise PermissionDenied("Модераторы не могут удалять курсы")

        if course.owner != request.user:
            raise PermissionDenied("Вы можете удалять только свои курсы")

        course.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_object(self, pk):
        """Вспомогательный метод для получения объекта"""
        try:
            return Course.objects.get(pk=pk)
        except Course.DoesNotExist:
            raise PermissionDenied("Курс не найден")


class LessonListCreateView(generics.ListCreateAPIView):
    """
    Generic-класс для уроков:
    - получение списка уроков (модераторы видят все, обычные - только свои)
    - создание нового урока (только для не-модераторов)
    """
    serializer_class = LessonSerializer

    def get_permissions(self):
        """
        Определяем права доступа для разных методов
        """
        if self.request.method == 'GET':
            # Просмотр списка доступен всем авторизованным
            permission_classes = [IsAuthenticated]
        elif self.request.method == 'POST':
            # Создание урока запрещено модераторам
            permission_classes = [IsAuthenticated, ~IsModerator]
        else:
            permission_classes = [IsAuthenticated]

        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """
        Фильтруем queryset в зависимости от прав пользователя
        """
        if IsModerator().has_permission(self.request, self):
            # Модераторы видят все уроки
            return Lesson.objects.all()
        else:
            # Обычные пользователи видят только свои уроки
            return Lesson.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        """
        При создании урока привязываем его к создателю
        """
        serializer.save(owner=self.request.user)


class LessonRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """
    Generic-класс для уроков:
    - получение одного урока (модераторы могут любой, обычные - только свой)
    - обновление урока (модераторы могут любой, обычные - только свой)
    - удаление урока (модераторам запрещено, обычные - только свой)
    """
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Базовый queryset для получения объекта
        """
        return Lesson.objects.all()

    def get_object(self):
        """
        Переопределяем get_object для проверки прав доступа к объекту
        """
        obj = super().get_object()

        # Проверяем права доступа к объекту
        if self.request.method == 'DELETE':
            # Для удаления: только владелец (модераторам запрещено)
            if IsModerator().has_permission(self.request, self):
                raise PermissionDenied("Модераторы не могут удалять уроки")
            if obj.owner != self.request.user:
                raise PermissionDenied("Вы можете удалять только свои уроки")
        else:
            # Для просмотра и редактирования: модератор ИЛИ владелец
            if not (IsModerator().has_permission(self.request, self) or obj.owner == self.request.user):
                raise PermissionDenied("У вас нет прав для доступа к этому уроку")

        return obj

    def perform_update(self, serializer):
        """
        При обновлении сохраняем владельца (не меняем)
        """
        serializer.save()