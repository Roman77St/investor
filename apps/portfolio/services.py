from decimal import Decimal
from django.db import transaction
from django.shortcuts import get_object_or_404
from apps.portfolio.models import Portfolio, Asset, Transaction
from apps.market.models import Stock
import logging

logger = logging.getLogger(__name__)

COMMISSION_RATE = Decimal('0.001')  # 0.1%

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
        stock_cost = current_price * quantity
        commission = stock_cost * COMMISSION_RATE
        # Общая сумма, которую списываем со счета
        total_debit = stock_cost + commission

        # 4. Проверяем баланс
        if portfolio.balance < total_debit:
            return {'success': False, 'error': f"Недостаточно средств. Требуется {total_debit:.2f} RUB(включая комиссию {commission:.2f}), доступно {portfolio.balance:.2f} RUB."}

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
        new_total_cost = stock_cost # В расчет средней цены комиссия НЕ входит
        new_quantity = asset.quantity + quantity

        # Формула взвешенной средней цены (Weighted Average Cost):
        new_average_price = (old_total_cost + new_total_cost) / new_quantity

        # 7. Обновляем Asset и баланс
        asset.quantity = new_quantity
        asset.average_buy_price = new_average_price
        asset.save()

        portfolio.balance -= total_debit
        portfolio.save()

        # 8. Создаем запись о транзакции
        Transaction.objects.create(
            portfolio=portfolio,
            stock=stock,
            action='BUY',
            quantity=quantity,
            price=current_price,
            commission=commission,
            # Примечание: Мы могли бы создать отдельную модель для учета комиссии,
            # но для MVP просто фиксируем комиссию в логе.
        )

        logger.info(f"{user.username} купил {quantity} шт. {ticker_symbol} по {current_price:.2f}. Комиссия: {commission:.2f}. Новая ср. цена: {new_average_price:.2f}.")

        return {'success': True, 'message': f"Куплено {quantity} шт. {ticker_symbol}. Списано {total_debit:.2f} RUB (в т.ч. комиссия {commission:.2f})."}

    @staticmethod
    @transaction.atomic
    def sell_stock(user, ticker_symbol: str, quantity: int) -> dict:
        """
        Обрабатывает продажу акций, включая расчет комиссии.
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
        stock_revenue = current_price * quantity
        commission = stock_revenue * COMMISSION_RATE

        total_credit = stock_revenue - commission

        asset.quantity -= quantity

        # 4. Обновляем баланс
        portfolio.balance += total_credit
        portfolio.save()

        # 5. Создаем запись о транзакции
        Transaction.objects.create(
            portfolio=portfolio,
            stock=stock,
            action='SELL',
            quantity=quantity,
            price=current_price,
            commission=commission,
        )

        # 6. Удаляем Asset, если она обнуляется
        if asset.quantity == 0:
            asset.delete()
            message = f"Продано {quantity} шт. {ticker_symbol}. Получено {total_credit:.2f} RUB (вычтена комиссия {commission:.2f}). Позиция закрыта."
        else:
            asset.save()
            message = f"Продано {quantity} шт. {ticker_symbol}. Получено {total_credit:.2f} RUB (вычтена комиссия {commission:.2f}). Остаток: {asset.quantity} шт."

        logger.info(f"{user.username} продал {quantity} шт. {ticker_symbol} по {current_price:.2f}. Комиссия: {commission:.2f}.")

        return {'success': True, 'message': message}

    @staticmethod
    def get_portfolio_summary(user) -> dict:
        """
        Возвращает сводку по портфелю пользователя, включая текущую стоимость,
        включая P&L в абсолютных числах и процентах.
        """
        portfolio = PortfolioService.get_user_portfolio(user)
        assets = portfolio.assets.select_related('stock') # Оптимизация

        total_market_value = Decimal('0.00')
        total_cost_basis = Decimal('0.00') # Сколько реально потрачено денег
        total_profit_loss = Decimal('0.00')
        asset_details = []

        for asset in assets:
            stock = asset.stock
            # Текущая рыночная стоимость
            market_value = asset.quantity * stock.current_price

            # Сколько было потрачено на покупку (Cost Basis)
            cost_basis = asset.quantity * asset.average_buy_price

            # Прибыль/Убыток по активу в деньгах
            profit_loss = market_value - cost_basis

            # Расчет P&L % для АКТИВА Формула: (P&L / Cost Basis) * 100
            profit_loss_percent = Decimal('0.00')
            if cost_basis > 0:
                profit_loss_percent = (profit_loss / cost_basis) * Decimal('100.00')

            total_market_value += market_value
            total_cost_basis += cost_basis
            total_profit_loss += profit_loss

            asset_details.append({
                'ticker': stock.ticker,
                'name': stock.name,
                'quantity': asset.quantity,
                'current_price': stock.current_price,
                'average_buy_price': asset.average_buy_price,
                'market_value': market_value,
                'profit_loss': profit_loss,
                'profit_loss_percent': profit_loss_percent,
                'lot_size': stock.lot_size,
            })

        # Расчет Общего P&L % для ПОРТФЕЛЯ
        total_profit_loss_percent = Decimal('0.00')
        if total_cost_basis > 0:
            total_profit_loss_percent = (total_profit_loss / total_cost_basis) * Decimal('100.00')

        return {
            'balance': portfolio.balance,
            'total_market_value': total_market_value,
            'total_cost_basis': total_cost_basis,
            'net_worth': portfolio.balance + total_market_value, # Чистая стоимость (Баланс + Акции)
            'total_profit_loss': total_profit_loss,
            'total_profit_loss_percent': total_profit_loss_percent,
            'assets': asset_details,
        }

    @staticmethod
    def get_transaction_history(user, limit=50) -> list:
        """
        Возвращает историю транзакций пользователя.
        """
        portfolio = PortfolioService.get_user_portfolio(user)

        # Получаем транзакции, связанные с портфелем, сортируем по дате,
        # и подтягиваем связанные акции для оптимизации.
        transactions = Transaction.objects.filter(
            portfolio=portfolio
        ).select_related(
            'stock'
        ).order_by(
            '-timestamp' # Сначала самые новые
        )[:limit]

        # Сериализуем данные вручную (для простоты, без DRF Serializers)
        history = []
        for tx in transactions:
            transaction_value = tx.price * tx.quantity
            history.append({
                'id': tx.id,
                'action': tx.get_action_display(), # 'Покупка' или 'Продажа'
                'ticker': tx.stock.ticker if tx.stock else 'Удалено',
                'quantity': tx.quantity,
                'price': tx.price,
                'total': transaction_value,
                'commission': tx.commission,
                'timestamp': tx.timestamp.isoformat(),
            })

        return history