from rest_framework.serializers import ModelSerializer
from .models import Stock

class StockSearchSerializer(ModelSerializer):
    class Meta:
        model = Stock
        fields = ['ticker', 'name']

class MarketStockSerializer(ModelSerializer):
    """
    Сериализатор для полного списка акций на странице "Рынок"
    """
    class Meta:
        model = Stock
        fields = ['ticker', 'name', 'current_price']