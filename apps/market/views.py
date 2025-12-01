from rest_framework import generics, permissions
from rest_framework.response import Response
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
    Возвращает полный список доступных акций с ценами.
    """
    serializer_class = MarketStockSerializer
    permission_classes = (permissions.IsAuthenticated,)

    queryset = Stock.objects.all().order_by('ticker')
