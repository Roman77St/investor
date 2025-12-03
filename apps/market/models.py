from django.db import models

# Акции
class Stock(models.Model):

    LISTING_LEVEL_CHOICES = [
        ('1', 'Первый'),
        ('2', 'Второй'),
        ('3', 'Третий'),
        # MOEX также использует 'V' для внесписочных бумаг, можно добавить при необходимости
    ]

    STOCK_TYPE_CHOICES = [
        ('COMMON', 'Обыкновенная'),
        ('PREFERRED', 'Привилегированная'),
    ]

    SECTOR_CHOICES = [
        ('OGAS', 'Нефть и Газ'),
        ('FINS', 'Финансовый сектор'),
        ('MTLS', 'Металлургия и Добыча'),
        ('TLCM', 'Телекоммуникации'),
        ('RTIL', 'Потребительский сектор'),
        ('IT', 'Информационные технологии'),
        ('ELC', 'Электроэнергетика'),
        ('OTHR', 'Прочее'),
    ]

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
    listing_level = models.CharField(
        max_length=1,
        choices=LISTING_LEVEL_CHOICES,
        default='3',
        blank=True,
        null=True,
        verbose_name="Уровень листинга"
    )

    sector = models.CharField(
        max_length=50,
        choices=SECTOR_CHOICES,
        default='OTHR',
        blank=True,
        null=True,
        verbose_name="Сектор"
    )

    is_blue_chip = models.BooleanField(
        default=False,
        verbose_name="Голубая фишка"
    )

    stock_type = models.CharField(
        max_length=15,
        choices=STOCK_TYPE_CHOICES,
        default='COMMON',
        verbose_name="Тип акции"
    )
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления цены")

    class Meta:
        verbose_name = "Акция"
        verbose_name_plural = "Акции"

    def __str__(self):
        return f"{self.ticker} - {self.current_price} RUB"