
from rest_framework.permissions import BasePermission

class IsModerator(BasePermission):
    """
    Проверка, является ли пользователь модератором
    """
    def has_permission(self, request, view):
        # Проверяем, что пользователь авторизован и состоит в группе "Модераторы"
        return request.user and request.user.is_authenticated and request.user.groups.filter(name='Модераторы').exists()


class IsOwner(BasePermission):
    """
    Проверка, является ли пользователь владельцем объекта
    """
    def has_object_permission(self, request, view, obj):
        # Проверяем, что у объекта есть поле owner и оно совпадает с текущим пользователем
        return obj.owner == request.user