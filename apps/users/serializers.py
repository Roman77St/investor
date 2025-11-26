from djoser.serializers import UserCreateSerializer, UserSerializer
from django.contrib.auth import get_user_model

User = get_user_model()

# 1. Сериализатор для регистрации (создания) пользователя
class CustomUserCreateSerializer(UserCreateSerializer):
    class Meta(UserCreateSerializer.Meta):
        # 💡 Явно указываем, что используем вашу модель User
        model = User
        fields = ('id', 'username', 'password')
        # Добавьте сюда любые кастомные поля, если они у вас есть

# 2. Сериализатор для отображения данных пользователя (профиль)
class CustomUserSerializer(UserSerializer):
    class Meta(UserSerializer.Meta):
        # 💡 Явно указываем, что используем вашу модель User
        model = User
        fields = ('id', 'username')
        # Добавьте сюда любые кастомные поля