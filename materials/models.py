# materials/models.py

from django.db import models
from django.conf import settings  # для получения модели пользователя


class Course(models.Model):
    """
    Модель курса
    """
    title = models.CharField(
        max_length=200,
        verbose_name='Название'
    )
    preview = models.ImageField(
        upload_to='courses/previews/',
        verbose_name='Превью',
        blank=True,
        null=True
    )
    description = models.TextField(
        verbose_name='Описание',
        blank=True
    )

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='courses',
        verbose_name='Владелец'
    )

    class Meta:
        verbose_name = 'Курс'
        verbose_name_plural = 'Курсы'

    def __str__(self):
        return self.title


class Lesson(models.Model):
    """
    Модель урока
    """
    title = models.CharField(
        max_length=200,
        verbose_name='Название'
    )
    description = models.TextField(
        verbose_name='Описание',
        blank=True
    )
    preview = models.ImageField(
        upload_to='lessons/previews/',
        verbose_name='Превью',
        blank=True,
        null=True
    )
    video_link = models.URLField(
        verbose_name='Ссылка на видео',
        blank=True,
        null=True
    )

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='lessons',
        verbose_name='Курс'
    )

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lessons',
        verbose_name='Владелец'
    )

    class Meta:
        verbose_name = 'Урок'
        verbose_name_plural = 'Уроки'

    def __str__(self):
        return self.title


class Subscription(models.Model):
    """
    Модель подписки пользователя на обновления курса
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name='Пользователь'
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name='Курс'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата подписки'
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        # Уникальность пары пользователь-курс (чтобы нельзя было подписаться дважды)
        unique_together = ('user', 'course')

    def __str__(self):
        return f'{self.user.email} подписан на {self.course.title}'