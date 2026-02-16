
from rest_framework.pagination import PageNumberPagination


class CoursePaginator(PageNumberPagination):
    """
    Пагинатор для списка курсов
    """
    page_size = 2  # Количество элементов на странице по умолчанию
    page_size_query_param = 'page_size'  # Параметр запроса для изменения количества элементов
    max_page_size = 10  # Максимально количество элементов на странице


class LessonPaginator(PageNumberPagination):
    """
    Пагинатор для списка уроков
    """
    page_size = 3  # Количество элементов на странице по умолчанию
    page_size_query_param = 'page_size'  # Параметр запроса для изменения количества элементов
    max_page_size = 15  # Максимально количество элементов на странице