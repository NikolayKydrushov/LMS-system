
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from materials.models import Course, Lesson


class Command(BaseCommand):
    help = 'Создание группы модераторов и назначение прав'

    def handle(self, *args, **kwargs):
        # Создаем группу модераторов
        moder_group, created = Group.objects.get_or_create(name='Модераторы')

        if created:
            self.stdout.write(self.style.SUCCESS('Группа "Модераторы" создана'))
        else:
            self.stdout.write(self.style.WARNING('Группа "Модераторы" уже существует'))

        # Получаем content types для моделей
        course_content_type = ContentType.objects.get_for_model(Course)
        lesson_content_type = ContentType.objects.get_for_model(Lesson)

        # Определяем права для модераторов
        # Модераторы могут просматривать и редактировать, но не создавать и не удалять

        # Права для курсов
        course_permissions = [
            'view_course',  # Просмотр
            'change_course',  # Редактирование
        ]

        # Права для уроков
        lesson_permissions = [
            'view_lesson',  # Просмотр
            'change_lesson',  # Редактирование
        ]

        # Очищаем старые права (чтобы обновить, если меняли)
        moder_group.permissions.clear()

        # Добавляем права на просмотр курсов
        for codename in course_permissions:
            try:
                permission = Permission.objects.get(
                    content_type=course_content_type,
                    codename=codename
                )
                moder_group.permissions.add(permission)
                self.stdout.write(f'Добавлено право: {codename}')
            except Permission.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Право {codename} не найдено'))

        # Добавляем права на просмотр уроков
        for codename in lesson_permissions:
            try:
                permission = Permission.objects.get(
                    content_type=lesson_content_type,
                    codename=codename
                )
                moder_group.permissions.add(permission)
                self.stdout.write(f'Добавлено право: {codename}')
            except Permission.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Право {codename} не найдено'))

        self.stdout.write(
            self.style.SUCCESS(f'Группа "Модераторы" настроена. Всего прав: {moder_group.permissions.count()}')
        )