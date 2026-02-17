
from rest_framework import serializers
from materials.models import Course, Lesson, Subscription, Payment
from materials.validators import validate_youtube_url


class SubscriptionSerializer(serializers.ModelSerializer):
    """
    Сериализатор для подписки
    """
    class Meta:
        model = Subscription
        fields = ('id', 'user', 'course', 'created_at')
        read_only_fields = ('user', 'created_at')  # user проставляется автоматически


class LessonSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели урока
    """

    # Переопределяем поле video и добавляем наш валидатор
    video = serializers.URLField(
        validators=[validate_youtube_url],
        required=False,  # Если поле необязательное
        allow_blank=True,  # Разрешаем пустую строку
    )

    class Meta:
        model = Lesson
        fields = '__all__'  # Включаем все поля модели


class CourseSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели курса
    """

    lessons_count = serializers.SerializerMethodField()
    lessons = LessonSerializer(many=True, read_only=True)
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = '__all__'  # Включаем все поля модели

    def get_lessons_count(self, obj):
        """
        Метод для SerializerMethodField.
        Возвращает количество уроков для конкретного курса.
        """
        return obj.lessons.count()

    def get_is_subscribed(self, obj):
        """
        Проверяет, подписан ли текущий пользователь на этот курс
        """
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            # Проверяем наличие подписки для текущего пользователя
            return Subscription.objects.filter(
                user=request.user,
                course=obj
            ).exists()
        return False


class PaymentSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели платежа
    """
    course_title = serializers.CharField(source='course.title', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model = Payment
        fields = [
            'id', 'user', 'user_email', 'course', 'course_title',
            'amount', 'payment_method', 'status', 'payment_url',
            'stripe_session_id', 'created_at'
        ]
        read_only_fields = [
            'user', 'status', 'payment_url', 'stripe_session_id',
            'stripe_product_id', 'stripe_price_id', 'created_at'
        ]


class PaymentCreateSerializer(serializers.ModelSerializer):
    """
    Сериализатор для создания платежа
    """

    class Meta:
        model = Payment
        fields = ['course', 'amount', 'payment_method']

    def validate(self, data):
        """
        Проверяем, что курс существует и не принадлежит текущему пользователю
        """
        request = self.context.get('request')
        course = data.get('course')

        # Проверка на покупку своего курса
        if course.owner == request.user:
            raise serializers.ValidationError(
                "Вы не можете оплатить свой собственный курс"
            )

        # Проверяем, нет ли уже оплаченного платежа за этот курс
        existing_payment = Payment.objects.filter(
            user=request.user,
            course=course,
            status=Payment.PaymentStatus.PAID
        ).exists()

        if existing_payment:
            raise serializers.ValidationError(
                "Вы уже оплатили этот курс"
            )

        return data

