from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

# 1. Наследуем от стандартного класса UserAdmin
# Это гарантирует, что все страницы управления пользователями (права, группы, пароль)
# будут работать корректно.
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    # 2. Обновляем наборы полей (fieldsets), чтобы добавить наше новое поле telegram_id.
    # Если этого не сделать, поле будет в базе, но не будет отображаться в форме редактирования.
    fieldsets = UserAdmin.fieldsets + (
        ('Информация Telegram', {'fields': ('telegram_id',)}),
    )

    # 3. Обновляем список отображаемых полей, чтобы telegram_id был виден на странице списка пользователей.
    list_display = UserAdmin.list_display + ('telegram_id',)

    # 4. Также можно добавить новое поле в форму поиска
    search_fields = UserAdmin.search_fields + ('telegram_id',)