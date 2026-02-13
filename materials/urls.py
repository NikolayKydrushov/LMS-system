from django.urls import path, include
from rest_framework.routers import DefaultRouter
from materials.views import CourseViewSet, LessonListCreateView, LessonRetrieveUpdateDestroyView

# Настройка роутера для ViewSet курсов
router = DefaultRouter()
router.register(r'courses', CourseViewSet, basename='course')

urlpatterns = [
    path('', include(router.urls)),

    # Маршруты для уроков (Generic-классы)
    # GET /lessons/ - список уроков
    # POST /lessons/ - создание урока
    path('lessons/', LessonListCreateView.as_view(), name='lesson-list-create'),

    # GET /lessons/<id>/ - получение урока
    # PUT /lessons/<id>/ - полное обновление
    # PATCH /lessons/<id>/ - частичное обновление
    # DELETE /lessons/<id>/ - удаление
    path('lessons/<int:pk>/', LessonRetrieveUpdateDestroyView.as_view(), name='lesson-detail'),
]