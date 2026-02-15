from django.shortcuts import render
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, filters
# from rest_framework.permissions import IsAuthenticated
from users.models import Payment
from users.serializers import PaymentSerializer

# Create your views here.


class PaymentViewSet(viewsets.ModelViewSet):
    """
    ViewSet для работы с платежами с поддержкой фильтрации
    """
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    # permission_classes = [IsAuthenticated]  # Только для авторизованных

    # Подключаем бэкенды для фильтрации
    filter_backends = [
        DjangoFilterBackend,  # Для фильтрации по полям
        filters.OrderingFilter,  # Для сортировки
    ]

    # Поля, по которым можно фильтровать (точное совпадение)
    filterset_fields = [
        'paid_course',  # Фильтр по ID курса
        'paid_lesson',  # Фильтр по ID урока
        'payment_method',  # Фильтр по способу оплаты
    ]

    # Поля, по которым можно сортировать
    ordering_fields = [
        'payment_date',  # Сортировка по дате
        'amount',  # Можно еще и по сумме (дополнительно)
    ]

    # Сортировка по умолчанию
    ordering = ['-payment_date']  # Сначала новые платежи