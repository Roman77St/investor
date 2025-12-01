from rest_framework import generics, permissions
from django.db.models import Q
from django.db.models.functions import Lower
from .models import Stock
from .serializers import StockSearchSerializer

class StockSearchView(generics.ListAPIView):
    """
    Поиск акций по тикеру или названию.
    Доступно: /api/market/search/?q=SBER
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