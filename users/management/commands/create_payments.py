from django.core.management.base import BaseCommand
from users.models import User, Payment
from materials.models import Course, Lesson
from datetime import datetime, timedelta
import random

class Command(BaseCommand):
    help = 'Создание тестовых платежей'

    def handle(self, *args, **kwargs):
        # Проверяем, есть ли пользователи, курсы и уроки
        users = User.objects.all()
        courses = Course.objects.all()
        lessons = Lesson.objects.all()

        if not users.exists():
            self.stdout.write(self.style.ERROR('Нет пользователей в базе'))
            return

        if not courses.exists() or not lessons.exists():
            self.stdout.write(self.style.WARNING('Нет курсов или уроков'))
            return

        # Очищаем существующие платежи (опционально)
        Payment.objects.all().delete()

        # Создаем тестовые платежи
        for user in users:
            # Платеж за курс
            if courses.exists():
                course = random.choice(courses)
                Payment.objects.create(
                    user=user,
                    paid_course=course,
                    amount=random.uniform(1000, 50000),
                    payment_method=random.choice(['cash', 'transfer']),
                    payment_date=datetime.now() - timedelta(days=random.randint(1, 30))
                )

            # Платеж за урок
            if lessons.exists():
                lesson = random.choice(lessons)
                Payment.objects.create(
                    user=user,
                    paid_lesson=lesson,
                    amount=random.uniform(500, 5000),
                    payment_method=random.choice(['cash', 'transfer']),
                    payment_date=datetime.now() - timedelta(days=random.randint(1, 30))
                )

        self.stdout.write(
            self.style.SUCCESS(f'Успешно создано {Payment.objects.count()} платежей')
        )