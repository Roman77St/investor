from rest_framework import serializers

class TradeSerializer(serializers.Serializer):
    """Сериализатор для валидации данных при покупке/продаже."""

    ticker = serializers.CharField(
        max_length=10,
        required=True,
        error_messages={'required': 'Необходимо указать тикер акции.'}
    )

    quantity = serializers.IntegerField(
        min_value=1,
        required=True,
        error_messages={'required': 'Необходимо указать количество акций.'}
    )

    def validate_ticker(self, value):
        """Преобразует тикер в верхний регистр для единообразия."""
        return value.upper()

    def validate_quantity(self, value):
        """Проверяет, что количество является положительным."""
        if value <= 0:
            raise serializers.ValidationError("Количество акций должно быть положительным числом.")
        return value