from django.contrib import admin
from users.models import User

# Register your models here.

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'phone', 'city', 'is_staff')
    list_filter = ('is_staff', 'is_active')
    search_fields = ('email', 'phone')

