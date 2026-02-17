from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status, generics
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from rest_framework.views import APIView
from materials.models import Course, Lesson, Subscription, Payment
from materials.serializers import (
    CourseSerializer,
    LessonSerializer,
    SubscriptionSerializer, PaymentCreateSerializer, PaymentSerializer
)
from materials.paginators import CoursePaginator, LessonPaginator
from materials.services.payment_service import PaymentService
from users.permissions import IsModerator, IsOwner

from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes


@extend_schema_view(
    list=extend_schema(
        summary="Список курсов",
        description="Возвращает список курсов. Модераторы видят все курсы, обычные пользователи - только свои.",
        responses={200: CourseSerializer(many=True)},
        tags=['Курсы']
    ),
    retrieve=extend_schema(
        summary="Детальная информация о курсе",
        description="Получение подробной информации о конкретном курсе по ID.",
        responses={200: CourseSerializer, 403: OpenApiTypes.OBJECT},
        tags=['Курсы']
    ),
    create=extend_schema(
        summary="Создание курса",
        description="Создание нового курса. Доступно только для пользователей без прав модератора.",
        request=CourseSerializer,
        responses={201: CourseSerializer, 400: OpenApiTypes.OBJECT},
        tags=['Курсы']
    ),
    update=extend_schema(
        summary="Полное обновление курса",
        description="Полное обновление информации о курсе.",
        request=CourseSerializer,
        responses={200: CourseSerializer, 403: OpenApiTypes.OBJECT},
        tags=['Курсы']
    ),
    partial_update=extend_schema(
        summary="Частичное обновление курса",
        description="Частичное обновление информации о курсе.",
        request=CourseSerializer,
        responses={200: CourseSerializer, 403: OpenApiTypes.OBJECT},
        tags=['Курсы']
    ),
    destroy=extend_schema(
        summary="Удаление курса",
        description="Удаление курса. Доступно только владельцу курса, модераторам запрещено.",
        responses={204: None, 403: OpenApiTypes.OBJECT},
        tags=['Курсы']
    ),
)
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

    # Пагинатор для курсов
    pagination_class = CoursePaginator

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
        """Получение списка всех курсов с пагинацией"""
        if IsModerator().has_permission(request, self):
            queryset = Course.objects.all().order_by('-id')  # Добавлена сортировка
        else:
            queryset = Course.objects.filter(owner=request.user).order_by('-id')

        # Применяем пагинацию
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request)

        if page is not None:
            serializer = CourseSerializer(
                page,
                many=True,
                context={'request': request}
            )
            return paginator.get_paginated_response(serializer.data)

        # Если пагинация отключена (на всякий случай)
        serializer = CourseSerializer(
            queryset,
            many=True,
            context={'request': request}
        )
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        """Получение одного курса по ID"""
        queryset = Course.objects.all()
        course = get_object_or_404(queryset, pk=pk)

        if not (IsModerator().has_permission(request, self) or course.owner == request.user):
            raise PermissionDenied("У вас нет прав для просмотра этого курса")

        # Передаем request в контекст сериализатора
        serializer = CourseSerializer(
            course,
            context={'request': request}  # Добавляем контекст
        )
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


@extend_schema_view(
    get=extend_schema(
        summary="Список уроков",
        description="Возвращает список уроков с пагинацией. Модераторы видят все уроки, обычные пользователи - только свои.",
        responses={200: LessonSerializer(many=True)},
        tags=['Уроки']
    ),
    post=extend_schema(
        summary="Создание урока",
        description="Создание нового урока. Доступно только для пользователей без прав модератора.",
        request=LessonSerializer,
        responses={201: LessonSerializer, 400: OpenApiTypes.OBJECT},
        tags=['Уроки']
    ),
)
class LessonListCreateView(generics.ListCreateAPIView):
    """
    Generic-класс для уроков:
    - получение списка уроков (модераторы видят все, обычные - только свои)
    - создание нового урока (только для не-модераторов)
    """
    serializer_class = LessonSerializer
    pagination_class = LessonPaginator  # Пагинатор для уроков

    def get_permissions(self):
        """
        Определяем права доступа для разных методов
        """
        if self.request.method == 'GET':
            permission_classes = [IsAuthenticated]
        elif self.request.method == 'POST':
            permission_classes = [IsAuthenticated, ~IsModerator]
        else:
            permission_classes = [IsAuthenticated]

        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """
        Фильтруем queryset в зависимости от прав пользователя
        """
        if IsModerator().has_permission(self.request, self):
            return Lesson.objects.all().order_by('-id')
        else:
            return Lesson.objects.filter(owner=self.request.user).order_by('-id')

    def perform_create(self, serializer):
        """
        При создании урока привязываем его к создателю
        """
        serializer.save(owner=self.request.user)


@extend_schema_view(
    get=extend_schema(
        summary="Детальная информация об уроке",
        description="Получение подробной информации о конкретном уроке.",
        responses={200: LessonSerializer, 403: OpenApiTypes.OBJECT, 404: OpenApiTypes.OBJECT},
        tags=['Уроки']
    ),
    put=extend_schema(
        summary="Полное обновление урока",
        description="Полное обновление информации об уроке.",
        request=LessonSerializer,
        responses={200: LessonSerializer, 403: OpenApiTypes.OBJECT},
        tags=['Уроки']
    ),
    patch=extend_schema(
        summary="Частичное обновление урока",
        description="Частичное обновление информации об уроке.",
        request=LessonSerializer,
        responses={200: LessonSerializer, 403: OpenApiTypes.OBJECT},
        tags=['Уроки']
    ),
    delete=extend_schema(
        summary="Удаление урока",
        description="Удаление урока. Доступно только владельцу урока, модераторам запрещено.",
        responses={204: None, 403: OpenApiTypes.OBJECT, 404: OpenApiTypes.OBJECT},
        tags=['Уроки']
    ),
)
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
            if IsModerator().has_permission(self.request, self):
                raise PermissionDenied("Модераторы не могут удалять уроки")
            if obj.owner != self.request.user:
                raise PermissionDenied("Вы можете удалять только свои уроки")
        else:
            if not (IsModerator().has_permission(self.request, self) or obj.owner == self.request.user):
                raise PermissionDenied("У вас нет прав для доступа к этому уроку")

        return obj

    def perform_update(self, serializer):
        """
        При обновлении сохраняем владельца (не меняем)
        """
        serializer.save()



@extend_schema(
    tags=['Подписки']
)
class SubscriptionView(APIView):
    """
    Эндпоинт для управления подпиской на курс:
    - POST: подписаться на курс
    - DELETE: отписаться от курса
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Подписка на курс",
        description="Создает подписку текущего пользователя на указанный курс.",
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'course_id': {'type': 'integer', 'description': 'ID курса'}
                },
                'required': ['course_id']
            }
        },
        responses={
            201: SubscriptionSerializer,
            400: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT
        },
        examples=[
            OpenApiExample(
                'Пример запроса',
                value={'course_id': 1},
                request_only=True,
            )
        ]
    )
    def post(self, request, *args, **kwargs):
        """
        Подписка на курс
        Ожидаем JSON: {"course_id": 1}
        """
        course_id = request.data.get('course_id')

        if not course_id:
            return Response(
                {'error': 'Необходимо указать course_id'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Проверяем, существует ли курс
        try:
            course = Course.objects.get(id=course_id)
        except Course.DoesNotExist:
            return Response(
                {'error': 'Курс не найден'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Проверяем, есть ли уже подписка
        subscription, created = Subscription.objects.get_or_create(
            user=request.user,
            course=course
        )

        if created:
            serializer = SubscriptionSerializer(subscription)
            return Response(
                {
                    'message': f'Вы успешно подписались на курс "{course.title}"',
                    'subscription': serializer.data
                },
                status=status.HTTP_201_CREATED
            )
        else:
            return Response(
                {'error': 'Вы уже подписаны на этот курс'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @extend_schema(
        summary="Отписка от курса",
        description="Удаляет подписку текущего пользователя на указанный курс.",
        parameters=[
            OpenApiParameter(
                name='course_id',
                type=int,
                location=OpenApiParameter.QUERY,
                description='ID курса (можно также передать в теле запроса)',
                required=False,
            )
        ],
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'course_id': {'type': 'integer'}
                }
            }
        },
        responses={
            204: None,
            400: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT
        }
    )
    def delete(self, request, *args, **kwargs):
        """
        Отписка от курса
        Ожидаем JSON: {"course_id": 1} или получаем course_id из query params
        """
        # Можно получать course_id из тела запроса или из query параметров
        course_id = request.data.get('course_id') or request.query_params.get('course_id')

        if not course_id:
            return Response(
                {'error': 'Необходимо указать course_id'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Ищем и удаляем подписку
        deleted_count, _ = Subscription.objects.filter(
            user=request.user,
            course_id=course_id
        ).delete()

        if deleted_count > 0:
            return Response(
                {'message': 'Вы успешно отписались от курса'},
                status=status.HTTP_204_NO_CONTENT
            )
        else:
            return Response(
                {'error': 'Подписка не найдена'},
                status=status.HTTP_404_NOT_FOUND
            )


@extend_schema(
    tags=['Платежи']
)
class PaymentListCreateView(generics.ListCreateAPIView):
    """
    View для создания и просмотра платежей
    """
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return PaymentCreateSerializer
        return PaymentSerializer

    def get_queryset(self):
        """Возвращаем только платежи текущего пользователя"""
        return Payment.objects.filter(user=self.request.user).select_related('course', 'user')

    @extend_schema(
        summary="Создание платежа",
        description="Создает новый платеж и возвращает ссылку на оплату через Stripe",
        request=PaymentCreateSerializer,
        responses={
            201: PaymentSerializer,
            400: OpenApiTypes.OBJECT,
            403: OpenApiTypes.OBJECT
        }
    )
    def post(self, request, *args, **kwargs):
        """Создание платежа"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Создаем платеж через сервис
        payment_data = PaymentService.create_payment(
            user=request.user,
            course=serializer.validated_data['course'],
            amount=serializer.validated_data['amount'],
            payment_method=serializer.validated_data.get('payment_method', 'card')
        )

        if payment_data['success']:
            response_serializer = PaymentSerializer(payment_data['payment'])
            return Response(
                {
                    'payment': response_serializer.data,
                    'payment_url': payment_data['payment_url']
                },
                status=status.HTTP_201_CREATED
            )
        else:
            return Response(
                {'error': payment_data['error']},
                status=status.HTTP_400_BAD_REQUEST
            )


@extend_schema(
    tags=['Платежи']
)
class PaymentDetailView(generics.RetrieveAPIView):
    """
    View для просмотра деталей платежа
    """
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Payment.objects.filter(user=self.request.user)


@extend_schema(
    tags=['Платежи'],
    parameters=[
        OpenApiParameter(
            name='payment_id',
            type=int,
            location=OpenApiParameter.PATH,
            description='ID платежа в системе'
        )
    ],
    responses={
        200: OpenApiTypes.OBJECT,
        400: OpenApiTypes.OBJECT,
        404: OpenApiTypes.OBJECT
    }
)
class PaymentStatusCheckView(APIView):
    """
    View для проверки статуса платежа
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, payment_id):
        """Проверка статуса платежа"""
        # Проверяем, принадлежит ли платеж текущему пользователю
        try:
            payment = Payment.objects.get(id=payment_id, user=request.user)
        except Payment.DoesNotExist:
            return Response(
                {'error': 'Платеж не найден'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Проверяем статус через сервис
        result = PaymentService.check_payment_status(payment_id)

        if result['success']:
            serializer = PaymentSerializer(result['payment'])
            return Response({
                'payment': serializer.data,
                'stripe_status': result.get('stripe_status')
            })
        else:
            return Response(
                {'error': result['error']},
                status=status.HTTP_400_BAD_REQUEST
            )


@extend_schema(
    tags=['Платежи'],
    parameters=[
        OpenApiParameter(
            name='session_id',
            type=str,
            location=OpenApiParameter.QUERY,
            description='ID сессии Stripe'
        )
    ],
    responses={
        200: OpenApiTypes.OBJECT,
        400: OpenApiTypes.OBJECT
    }
)
class PaymentSuccessView(APIView):
    """
    View для обработки успешной оплаты (редирект из Stripe)
    """
    permission_classes = []  # Открытый доступ для редиректов

    def get(self, request):
        session_id = request.GET.get('session_id')

        if not session_id:
            return Response(
                {'error': 'Session ID не предоставлен'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Ищем платеж по session_id
        try:
            payment = Payment.objects.get(stripe_session_id=session_id)
        except Payment.DoesNotExist:
            return Response(
                {'error': 'Платеж не найден'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Обновляем статус платежа
        payment.status = Payment.PaymentStatus.PAID
        payment.save()

        return Response({
            'message': 'Платеж успешно выполнен',
            'course_id': payment.course.id,
            'course_title': payment.course.title
        })


@extend_schema(
    tags=['Платежи'],
    responses={200: OpenApiTypes.OBJECT}
)
class PaymentCancelView(APIView):
    """
    View для обработки отмены оплаты
    """
    permission_classes = []

    def get(self, request):
        return Response({
            'message': 'Оплата была отменена'
        })