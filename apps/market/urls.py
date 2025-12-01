from django.urls import path
from .views import StockSearchView

urlpatterns = [
    # Маршрут: /api/market/search/
    path('search/', StockSearchView.as_view(), name='stock_search'),
]
