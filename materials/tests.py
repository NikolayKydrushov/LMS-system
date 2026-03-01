from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from materials.models import Course, Lesson, Subscription
from users.models import User


# Create your tests here.


class LessonCRUDTests(TestCase):
    """
    Тесты для CRUD операций с уроками
    """

    def setUp(self):
        """
        Метод setUp выполняется перед каждым тестом
        Заполняем базу тестовыми данными
        """
        # Создаем клиент для отправки запросов
        self.client = APIClient()

        # Создаем пользователей с разными ролями
        self.owner_user = User.objects.create_user(
            email='owner@test.com',
            password='testpass123',
            first_name='Owner',
            last_name='User'
        )

        self.other_user = User.objects.create_user(
            email='other@test.com',
            password='testpass123',
            first_name='Other',
            last_name='User'
        )

        self.moderator_user = User.objects.create_user(
            email='moderator@test.com',
            password='testpass123',
            first_name='Moderator',
            last_name='User',
        )

        # Создаем курс для привязки уроков
        self.course = Course.objects.create(
            title='Тестовый курс',
            description='Описание тестового курса',
            owner=self.owner_user
        )

        lesson_data = {
            'title': 'Тестовый урок',
            'description': 'Описание тестового урока',
            'course': self.course,
            'owner': self.owner_user
        }

        if hasattr(Lesson, 'video'):
            lesson_data['video'] = 'https://www.youtube.com/watch?v=12345'
        elif hasattr(Lesson, 'video_url'):
            lesson_data['video_url'] = 'https://www.youtube.com/watch?v=12345'
        elif hasattr(Lesson, 'link'):
            lesson_data['link'] = 'https://www.youtube.com/watch?v=12345'

        # Создаем урок для тестов
        self.lesson = Lesson.objects.create(**lesson_data)

        # Базовые URL для запросов
        self.lessons_url = '/api/lessons/'
        self.lesson_detail_url = f'/api/lessons/{self.lesson.id}/'

    def test_create_lesson_as_owner(self):
        """
        Тест: создание урока владельцем (должно работать)
        """
        # Аутентифицируем владельца
        self.client.force_authenticate(user=self.owner_user)

        # Данные для нового урока
        data = {
            'title': 'Новый урок',
            'description': 'Описание нового урока',
            'course': self.course.id
        }

        # Добавляем видео в зависимости от названия поля в модели
        if hasattr(Lesson, 'video'):
            data['video'] = 'https://www.youtube.com/watch?v=67890'
        elif hasattr(Lesson, 'video_url'):
            data['video_url'] = 'https://www.youtube.com/watch?v=67890'
        elif hasattr(Lesson, 'link'):
            data['link'] = 'https://www.youtube.com/watch?v=67890'

        # Отправляем POST запрос
        response = self.client.post(self.lessons_url, data, format='json')

        # Проверяем ответ
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'Новый урок')

        # Проверяем, что урок действительно создан в БД
        self.assertTrue(Lesson.objects.filter(title='Новый урок').exists())


    def test_list_lessons_as_owner(self):
        """
        Тест: получение списка уроков владельцем
        """
        self.client.force_authenticate(user=self.owner_user)
        response = self.client.get(self.lessons_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Проверяем структуру пагинированного ответа
        self.assertIn('results', response.data)
        self.assertIn('count', response.data)

        # Владелец видит свои уроки
        self.assertEqual(len(response.data['results']), 1)


    def test_list_lessons_as_other_user(self):
        """
        Тест: получение списка уроков другим пользователем
        (должен видеть только свои уроки, а их у него нет)
        """
        self.client.force_authenticate(user=self.other_user)
        response = self.client.get(self.lessons_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 0)


    def test_retrieve_lesson_as_owner(self):
        """
        Тест: получение конкретного урока владельцем
        """
        self.client.force_authenticate(user=self.owner_user)
        response = self.client.get(self.lesson_detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], self.lesson.title)


    def test_retrieve_lesson_as_other_user(self):
        """
        Тест: получение чужого урока другим пользователем (должен быть доступ запрещен)
        """
        self.client.force_authenticate(user=self.other_user)
        response = self.client.get(self.lesson_detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


    def test_update_lesson_as_owner(self):
        """
        Тест: обновление урока владельцем
        """
        self.client.force_authenticate(user=self.owner_user)

        updated_data = {
            'title': 'Обновленный заголовок',
            'description': 'Новое описание',
            'course': self.course.id
        }

        response = self.client.put(self.lesson_detail_url, updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Проверяем, что данные обновились
        self.lesson.refresh_from_db()
        self.assertEqual(self.lesson.title, 'Обновленный заголовок')


    def test_update_lesson_as_other_user(self):
        """
        Тест: обновление чужого урока другим пользователем (должен быть запрет)
        """
        self.client.force_authenticate(user=self.other_user)

        updated_data = {
            'title': 'Попытка взлома',
            'course': self.course.id
        }

        response = self.client.put(self.lesson_detail_url, updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


    def test_delete_lesson_as_owner(self):
        """
        Тест: удаление урока владельцем
        """
        self.client.force_authenticate(user=self.owner_user)
        response = self.client.delete(self.lesson_detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Проверяем, что урок действительно удален
        self.assertFalse(Lesson.objects.filter(id=self.lesson.id).exists())


    def test_delete_lesson_as_other_user(self):
        """
        Тест: удаление чужого урока другим пользователем (запрещено)
        """
        self.client.force_authenticate(user=self.other_user)
        response = self.client.delete(self.lesson_detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Lesson.objects.filter(id=self.lesson.id).exists())


class SubscriptionTests(TestCase):
    """
    Тесты для функционала подписки на курсы
    """

    def setUp(self):
        """
        Подготовка данных для тестов подписки
        """
        self.client = APIClient()

        # Создаем пользователей
        self.user1 = User.objects.create_user(
            email='user1@test.com',
            password='testpass123',
            first_name='User',
            last_name='One'
        )

        self.user2 = User.objects.create_user(
            email='user2@test.com',
            password='testpass123',
            first_name='User',
            last_name='Two'
        )

        # Создаем курсы
        self.course1 = Course.objects.create(
            title='Курс для подписки 1',
            description='Описание курса 1',
            owner=self.user1
        )

        self.course2 = Course.objects.create(
            title='Курс для подписки 2',
            description='Описание курса 2',
            owner=self.user1
        )

        # URL для подписок
        self.subscriptions_url = '/api/subscriptions/'
        self.courses_url = '/api/courses/'


    def test_subscribe_to_course(self):
        """
        Тест: подписка пользователя на курс
        """
        self.client.force_authenticate(user=self.user2)
        data = {'course_id': self.course1.id}
        response = self.client.post(self.subscriptions_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Проверяем, что подписка создана в БД
        self.assertTrue(
            Subscription.objects.filter(
                user=self.user2,
                course=self.course1
            ).exists()
        )


    def test_unsubscribe_from_course(self):
        """
        Тест: отписка от курса
        """
        self.client.force_authenticate(user=self.user2)

        # Сначала подписываемся
        Subscription.objects.create(
            user=self.user2,
            course=self.course1
        )

        # Отписываемся
        response = self.client.delete(
            f'{self.subscriptions_url}?course_id={self.course1.id}'
        )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Проверяем, что подписки больше нет
        self.assertFalse(
            Subscription.objects.filter(
                user=self.user2,
                course=self.course1
            ).exists()
        )



class LessonPaginationTests(TestCase):
    """
    Тесты для проверки пагинации уроков
    """

    def setUp(self):
        self.client = APIClient()

        self.user = User.objects.create_user(
            email='user@test.com',
            password='testpass123'
        )

        self.course = Course.objects.create(
            title='Курс для пагинации',
            description='Описание',
            owner=self.user
        )

        # Создаем 5 уроков для теста пагинации
        for i in range(5):
            lesson_data = {
                'title': f'Урок {i + 1}',
                'course': self.course,
                'owner': self.user
            }

            # Добавляем видео в зависимости от названия поля в модели
            if hasattr(Lesson, 'video'):
                lesson_data['video'] = 'https://www.youtube.com/watch?v=12345'
            elif hasattr(Lesson, 'video_url'):
                lesson_data['video_url'] = 'https://www.youtube.com/watch?v=12345'
            elif hasattr(Lesson, 'link'):
                lesson_data['link'] = 'https://www.youtube.com/watch?v=12345'

            Lesson.objects.create(**lesson_data)

        self.lessons_url = '/api/lessons/'


    def test_lesson_pagination_default_page_size(self):
        """
        Тест: проверка размера страницы по умолчанию
        """
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.lessons_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 3)  # page_size = 3


    def test_lesson_pagination_second_page(self):
        """
        Тест: проверка второй страницы пагинации
        """
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f'{self.lessons_url}?page=2')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)  # Оставшиеся 2 урока


    def test_lesson_pagination_custom_page_size(self):
        """
        Тест: изменение количества элементов на странице через параметр
        """
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f'{self.lessons_url}?page_size=2')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
