from django.shortcuts import render
from django.contrib.auth import get_user_model  # Добавляем этот импорт
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, filters, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from users.models import Payment
from users.serializers import (
    PaymentSerializer,
    RegisterSerializer,
    UserSerializer
)

# Получаем модель пользователя
User = get_user_model()


class PaymentViewSet(viewsets.ModelViewSet):
    """
    ViewSet для работы с платежами с поддержкой фильтрации
    """
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    # permission_classes = [IsAuthenticated]

    filter_backends = [
        DjangoFilterBackend,
        filters.OrderingFilter,
    ]

    filterset_fields = [
        'paid_course',
        'paid_lesson',
        'payment_method',
    ]

    ordering_fields = [
        'payment_date',
        'amount',
    ]

    ordering = ['-payment_date']


@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """
    Регистрация нового пользователя
    """
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()

        refresh = RefreshToken.for_user(user)

        return Response({
            'user': UserSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_list(request):
    """
    Список всех пользователей
    """
    users = User.objects.all()  # User.objects
    serializer = UserSerializer(users, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_detail(request, pk):
    """
    Детальная информация о пользователе
    """
    try:
        user = User.objects.get(pk=pk)  # User.objects
    except User.DoesNotExist:
        return Response(
            {'error': 'Пользователь не найден'},
            status=status.HTTP_404_NOT_FOUND
        )

    serializer = UserSerializer(user)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def current_user(request):
    """
    Информация о текущем авторизованном пользователе
    """
    serializer = UserSerializer(request.user)
    return Response(serializer.data)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def user_update(request, pk):
    """
    Обновление данных пользователя
    """
    try:
        user = User.objects.get(pk=pk)  # User.objects
    except User.DoesNotExist:
        return Response(
            {'error': 'Пользователь не найден'},
            status=status.HTTP_404_NOT_FOUND
        )

    if request.user.id != user.id and not request.user.is_staff:
        return Response(
            {'error': 'Вы можете редактировать только свой профиль'},
            status=status.HTTP_403_FORBIDDEN
        )

    partial = request.method == 'PATCH'
    serializer = UserSerializer(user, data=request.data, partial=partial)

    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def user_delete(request, pk):
    """
    Удаление пользователя
    """
    try:
        user = User.objects.get(pk=pk)  # User.objects
    except User.DoesNotExist:
        return Response(
            {'error': 'Пользователь не найден'},
            status=status.HTTP_404_NOT_FOUND
        )

    if request.user.id != user.id and not request.user.is_staff:
        return Response(
            {'error': 'Вы можете удалить только свой профиль'},
            status=status.HTTP_403_FORBIDDEN
        )

    user.delete()
    return Response(
        {'message': 'Пользователь успешно удален'},
        status=status.HTTP_204_NO_CONTENT
    )