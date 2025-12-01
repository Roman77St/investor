from rest_framework import serializers
from .models import Stock

class StockSearchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stock
        fields = ['ticker', 'name']