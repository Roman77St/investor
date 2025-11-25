from django.db import models

# Акции
class Stock(models.Model):
    # Тикер — краткое буквенное или буквенно-цифровое обозначение ценной бумаги или индекса на бирже.
    ticker = models.CharField(max_length=10, unique=True, verbose_name='Тикер (SBER)')
    name = models.CharField(max_length=100, verbose_name="Название компании")
    # Кэшируем цену, чтобы не дергать API каждую секунду при просмотре портфеля
    current_price = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0.00,
        verbose_name="Текущая цена"
    )
    lot_size = models.PositiveIntegerField(default=1, verbose_name="Размер лота")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления цены")

    class Meta:
        verbose_name = "Акция"
        verbose_name_plural = "Акции"

    def __str__(self):
        return f"{self.ticker} - {self.current_price} RUB"