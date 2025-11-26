from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TradingViewSet, PortfolioViewSet

router = DefaultRouter()
# /api/portfolio/trade/buy/ и /api/portfolio/trade/sell/
router.register(r'trade', TradingViewSet, basename='trade')
# 💡 /api/portfolio/summary/ (благодаря @action(detail=False, methods=['get']) на PortfolioViewSet)
router.register(r'', PortfolioViewSet, basename='portfolio')

urlpatterns = [
    path('', include(router.urls)),
]