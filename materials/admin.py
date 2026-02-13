from django.contrib import admin
from materials.models import Course, Lesson

# Register your models here.


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'id')
    search_fields = ('title',)

@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'id')
    list_filter = ('course',)
    search_fields = ('title',)

