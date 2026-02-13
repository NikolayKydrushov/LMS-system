from django.contrib.auth.models import AbstractUser
from django.db import models

# Create your models here.

class User(AbstractUser):
    """
    Кастомная модель пользователя с авторизацией по email
    """
    username = None  # Убираем поле username
    email = models.EmailField(unique=True, verbose_name='Email')
    phone = models.CharField(max_length=35, verbose_name='Телефон', blank=True, null=True)
    city = models.CharField(max_length=100, verbose_name='Город', blank=True, null=True)
    avatar = models.ImageField(upload_to='users/avatars/', verbose_name='Аватар', blank=True, null=True)

    USERNAME_FIELD = 'email'  # Теперь авторизация по email
    REQUIRED_FIELDS = []  # Обязательные поля при создании superuser (кроме email и пароля)

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.email

