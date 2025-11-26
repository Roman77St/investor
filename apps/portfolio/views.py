import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .serializers import TradeSerializer
from .services import PortfolioService

logger = logging.getLogger(__name__)

class TradingViewSet(viewsets.GenericViewSet):
    """
    ViewSet для обработки запросов на покупку/продажу акций.
    Доступен только для аутентифицированных пользователей.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = TradeSerializer

    @action(detail=False, methods=['post'])
    def buy(self, request):
        """Обрабатывает запрос на покупку акций."""
        serializer = self.get_serializer(data=request.data)

        # 1. Валидация входных данных (тикер, количество)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        ticker = serializer.validated_data['ticker']
        quantity = serializer.validated_data['quantity']
        user = request.user

        # 2. Вызов сервиса для выполнения транзакции
        result = PortfolioService.buy_stock(user, ticker, quantity)

        # 3. Ответ клиенту
        if result['success']:
            return Response({'message': result['message']}, status=status.HTTP_200_OK)
        else:
            # Ошибки баланса, лотности или отсутствия акции
            logger.warning(f"Ошибка покупки для пользователя {user.username}: {result['error']}")
            return Response({'error': result['error']}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def sell(self, request):
        """Обрабатывает запрос на продажу акций."""
        serializer = self.get_serializer(data=request.data)

        # 1. Валидация входных данных (тикер, количество)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        ticker = serializer.validated_data['ticker']
        quantity = serializer.validated_data['quantity']
        user = request.user

        # 2. Вызов сервиса для выполнения транзакции
        result = PortfolioService.sell_stock(user, ticker, quantity)

        # 3. Ответ клиенту
        if result['success']:
            return Response({'message': result['message']}, status=status.HTTP_200_OK)
        else:
            # Ошибки наличия позиций, лотности
            logger.warning(f"Ошибка продажи для пользователя {user.username}: {result['error']}")
            return Response({'error': result['error']}, status=status.HTTP_400_BAD_REQUEST)

class PortfolioViewSet(viewsets.GenericViewSet):
    """ViewSet для отображения сводки по портфелю."""
    permission_classes = [IsAuthenticated] # 🛡️ Защищаем точку токеном

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Возвращает полную сводку по портфелю, включая P&L."""

        # 1. Вызов сервиса для сбора и расчета данных
        summary_data = PortfolioService.get_portfolio_summary(request.user)

        # 2. Ответ клиенту
        return Response(summary_data, status=status.HTTP_200_OK)