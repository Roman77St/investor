from django.db import transaction
from django.shortcuts import get_object_or_404
from apps.portfolio.models import Portfolio, Asset, Transaction
from apps.market.models import Stock
import logging

logger = logging.getLogger(__name__)

class PortfolioService:

    @staticmethod
    def get_user_portfolio(user) -> Portfolio:
        """Получает или создает портфель пользователя."""
        # Используем get_or_create, чтобы гарантировать существование портфеля
        # (Начальный капитал 100000.00, как указано в модели)
        return Portfolio.objects.get_or_create(user=user)[0]

    @staticmethod
    @transaction.atomic
    def buy_stock(user, ticker_symbol: str, quantity: int) -> dict:
        """
        Обрабатывает покупку акций.
        Проверяет баланс и лотность, обновляет Asset и Portfolio, создает Transaction.
        """
        portfolio = PortfolioService.get_user_portfolio(user)

        # 1. Получаем Stock и проверяем, что он существует
        stock = get_object_or_404(Stock, ticker=ticker_symbol.upper())
        current_price = stock.current_price

        # 2. Проверяем лотность (количество должно быть кратно лоту)
        if quantity % stock.lot_size != 0:
            return {'success': False, 'error': f"Количество {quantity} должно быть кратно размеру лота: {stock.lot_size}."}

        # 3. Рассчитываем общую стоимость сделки
        total_cost = current_price * quantity

        # 4. Проверяем баланс
        if portfolio.balance < total_cost:
            return {'success': False, 'error': f"Недостаточно средств. Требуется {total_cost:.2f} RUB, доступно {portfolio.balance:.2f} RUB."}

        # --- Логика покупки ---

        # 5. Обновляем/Создаем Asset (позицию)
        asset, created = Asset.objects.get_or_create(
            portfolio=portfolio,
            stock=stock,
            # Defaults для созданной позиции
            defaults={'quantity': 0, 'average_buy_price': current_price}
        )

        # 6. Расчет новой взвешенной средней цены покупки
        old_total_cost = asset.average_buy_price * asset.quantity
        new_total_cost = total_cost
        new_quantity = asset.quantity + quantity

        # Формула взвешенной средней цены (Weighted Average Cost):
        new_average_price = (old_total_cost + new_total_cost) / new_quantity

        # 7. Обновляем Asset и баланс
        asset.quantity = new_quantity
        asset.average_buy_price = new_average_price
        asset.save()

        portfolio.balance -= total_cost
        portfolio.save()

        # 8. Создаем запись о транзакции
        Transaction.objects.create(
            portfolio=portfolio,
            stock=stock,
            action='BUY',
            quantity=quantity,
            price=current_price
        )

        logger.info(f"{user.username} купил {quantity} шт. {ticker_symbol} по {current_price:.2f}. Новая ср. цена: {new_average_price:.2f}.")

        return {'success': True, 'message': f"Куплено {quantity} шт. {ticker_symbol} по цене {current_price:.2f}. Счет обновлен."}

    @staticmethod
    @transaction.atomic
    def sell_stock(user, ticker_symbol: str, quantity: int) -> dict:
        """
        Обрабатывает продажу акций.
        Проверяет наличие, рассчитывает доход, обновляет Asset и Portfolio, создает Transaction.
        """
        portfolio = PortfolioService.get_user_portfolio(user)
        stock = get_object_or_404(Stock, ticker=ticker_symbol.upper())
        current_price = stock.current_price

        # 1. Получаем существующий Asset
        try:
            asset = Asset.objects.get(portfolio=portfolio, stock=stock)
        except Asset.DoesNotExist:
            return {'success': False, 'error': f"У вас нет акций {ticker_symbol} для продажи."}

        # 2. Проверяем лотность и достаточное количество
        if quantity % stock.lot_size != 0:
            return {'success': False, 'error': f"Количество {quantity} должно быть кратно размеру лота: {stock.lot_size}."}

        if asset.quantity < quantity:
            return {'success': False, 'error': f"Недостаточно акций. Доступно: {asset.quantity} шт."}

        # --- Логика продажи ---

        # 3. Рассчитываем доход и обновляем Asset
        revenue = current_price * quantity

        asset.quantity -= quantity

        # 4. Обновляем баланс
        portfolio.balance += revenue
        portfolio.save()

        # 5. Создаем запись о транзакции
        Transaction.objects.create(
            portfolio=portfolio,
            stock=stock,
            action='SELL',
            quantity=quantity,
            price=current_price
        )

        # 6. Удаляем Asset, если она обнуляется
        if asset.quantity == 0:
            asset.delete()
            message = f"Продано {quantity} шт. {ticker_symbol} по цене {current_price:.2f}. Позиция закрыта."
        else:
            asset.save()
            message = f"Продано {quantity} шт. {ticker_symbol} по цене {current_price:.2f}. Остаток: {asset.quantity} шт."

        logger.info(f"{user.username} продал {quantity} шт. {ticker_symbol} по {current_price:.2f}.")

        return {'success': True, 'message': message}