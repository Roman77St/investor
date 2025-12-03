from decimal import Decimal
from rest_framework import generics, permissions
from django.db.models import Q
from .models import Stock
from .serializers import StockSearchSerializer, MarketStockSerializer

class StockSearchView(generics.ListAPIView):
    """
    Поиск акций по тикеру или названию.
    Доступно: /api/market/search/?q=SBER
    Переделать полноценный поиск на postgres.
    """
    serializer_class = StockSearchSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        queryset = Stock.objects.all()
        query = self.request.query_params.get('q', None)
        if query:
            title_query = query.title()
            queryset = queryset.filter(Q(ticker__icontains=query) | Q(name__contains=query) | Q(name__contains=title_query))[:10]
        return queryset

class MarketListView(generics.ListAPIView):
    """
    Возвращает полный список доступных акций с ценами и поддерживает фильтрацию
    по сектору, уровню листинга, типу акции и статусу "Голубая фишка".
    """
    serializer_class = MarketStockSerializer
    permission_classes = (permissions.IsAuthenticated,)

    queryset = Stock.objects.all().order_by('ticker')

    def get_queryset(self):
        queryset = self.queryset
        params = self.request.query_params

        query = params.get('q', None)
        if query:
            title_query = query.title()
            queryset = queryset.filter(
                Q(ticker__icontains=query) |
                Q(name__contains=query) |
                Q(name__contains=title_query)
            )

        # --- 1. Фильтрация по Сектору (sector) ---
        # Ожидаемый параметр: ?sector=FINS
        sector = params.get('sector')
        if sector and sector != 'ALL':
            queryset = queryset.filter(sector=sector)

        # --- 2. Фильтрация по Уровню листинга (listing_level) ---
        # Ожидаемый параметр: ?listing_level=1
        listing_level = params.get('listing_level')
        if listing_level and listing_level != 'ALL':
            queryset = queryset.filter(listing_level=listing_level)

        # --- 3. Фильтрация по Типу акции (stock_type) ---
        # Ожидаемый параметр: ?stock_type=PREFERRED
        stock_type = params.get('stock_type')
        if stock_type and stock_type != 'ALL':
            queryset = queryset.filter(stock_type=stock_type)

        # --- 4. Фильтрация по Голубым фишкам (is_blue_chip) ---
        # Ожидаемый параметр: ?blue_chip=true
        blue_chip = params.get('blue_chip')
        if blue_chip == 'true':
            # Фильтруем только те, где is_blue_chip = True
            queryset = queryset.filter(is_blue_chip=True)

        # --- 5. Дополнительная фильтрация: Цена > 0 (для безопасности) ---
        # Это гарантирует, что мы не показываем "мертвые" акции, если они не были отфильтрованы
        queryset = queryset.exclude(Q(current_price__isnull=True) | Q(current_price__lte=Decimal('0')))

        return queryset