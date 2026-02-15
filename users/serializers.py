from rest_framework import serializers
from django.contrib.auth import get_user_model  # Добавляем этот импорт
from rest_framework.validators import UniqueValidator
from django.contrib.auth.password_validation import validate_password
from users.models import Payment

# Получаем активную модель пользователя
User = get_user_model()


class PaymentSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели платежа
    """
    class Meta:
        model = Payment
        fields = '__all__'


class RegisterSerializer(serializers.ModelSerializer):
    """
    Сериализатор для регистрации новых пользователей
    """
    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all())]  # Теперь работает
    )
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    password2 = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )

    class Meta:
        model = User
        fields = ('username', 'password', 'password2', 'email', 'first_name', 'last_name')

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({
                "password": "Пароли не совпадают"
            })
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(**validated_data)  # Используем User.objects
        return user


class UserSerializer(serializers.ModelSerializer):
    """
    Сериализатор для отображения информации о пользователях
    """
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'date_joined')
        read_only_fields = ('id', 'date_joined')