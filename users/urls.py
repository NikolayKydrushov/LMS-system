from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from users.views import (
    PaymentViewSet,
    register,
    user_list,
    user_detail,
    current_user,
    user_update,
    user_delete,
)

router = DefaultRouter()
router.register(r'payments', PaymentViewSet, basename='payment')

# URL-маршруты API
urlpatterns = [
    # Публичные эндпоинты (доступны без авторизации)
    path('register/', register, name='register'),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Защищенные эндпоинты (требуют JWT токен)
    # Эндпоинты пользователей
    path('users/', user_list, name='user-list'),
    path('users/me/', current_user, name='user-me'),
    path('users/<int:pk>/', user_detail, name='user-detail'),
    path('users/<int:pk>/update/', user_update, name='user-update'),
    path('users/<int:pk>/delete/', user_delete, name='user-delete'),

    # Существующий роутер для платежей (требует авторизацию)
    path('', include(router.urls)),
]

api_urlpatterns = [
    path('api/', include(urlpatterns)),
]

