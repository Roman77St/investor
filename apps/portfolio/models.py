from decimal import Decimal
from django.db import models
from django.conf import settings
from apps.market.models import Stock

# Кошелек пользователя.
class Portfolio(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='portfolio'
    )
    # Стартовый капитал 100 000
    balance = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal('100000.00'),
        verbose_name="Баланс (RUB)"
    )

    class Meta:
        verbose_name = 'портфель'
        verbose_name_plural = 'портфели'

    def __str__(self):
        return f"Портфель {self.user.username}"

# Каких акций и сколько у пользователя.
class Asset(models.Model):
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name='assets')
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name='assets')
    quantity = models.PositiveIntegerField(default=0, verbose_name="Количество акций")

    # Средняя цена покупки нужна, чтобы считать прибыль/убыток (P&L)
    average_buy_price = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0.00,
        verbose_name="Средняя цена покупки"
    )

    class Meta:
        unique_together = ('portfolio', 'stock') # Одна запись на один тикер в портфеле

    def __str__(self):
        return f"{self.stock.ticker}: {self.quantity} шт."

# История (купил/продал), чтобы пользователь видел, куда делись деньги.
class Transaction(models.Model):
    ACTION_CHOICES = (
        ('BUY', 'Покупка'),
        ('SELL', 'Продажа'),
    )

    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name='transactions')
    stock = models.ForeignKey(Stock, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=4, choices=ACTION_CHOICES)

    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=14, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'транзакция'
        verbose_name_plural = 'транзакции'


    def __str__(self):
        return f"{self.action} {self.stock.ticker} x {self.quantity}"