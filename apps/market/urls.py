from django.urls import path
from .views import StockSearchView, MarketListView

urlpatterns = [
    # Маршрут: /api/market/search/
    path('search/', StockSearchView.as_view(), name='stock_search'),
    path('list/', MarketListView.as_view(), name='market_list_api'),
]
