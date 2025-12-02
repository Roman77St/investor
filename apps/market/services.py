from decimal import Decimal
from moexalgo import Market, Ticker
from django.db import transaction
from django.utils import timezone
from .models import Stock
import logging

logger = logging.getLogger(__name__)

class MoexDataService:

    @staticmethod
    def initialize_top_stocks():
        """Инициализирует базу данных основными акциями, получает их реальные имена."""
        logger.info("Starting initial stock data population...")
        new_stocks_count = 0

        try:
            market = Market('shares', 'tqbr')
            # Получаем все метаданные ценных бумаг с доски TQBR
            security_list = market.tickers('*')

        except Exception as e:
            logger.error(f"FATAL: Could not fetch security list via Market.tickers(): {e}")
            return

        for sec_info in security_list:

            # Извлекаем данные
            ticker_symbol = sec_info.get('ticker')
            real_name = sec_info.get('shortname')
            fetched_lot_size = sec_info.get('lotsize', 1)

            # Базовая валидация: пропускаем, если нет тикера, имени или лот некорректен
            if not ticker_symbol or not real_name or fetched_lot_size is None or fetched_lot_size < 1:
                continue

            ticker_symbol = ticker_symbol.upper()

            # Используем get_or_createдля добавления новой акции
            stock, created = Stock.objects.get_or_create(
                ticker=ticker_symbol,
                defaults={
                    'name': real_name,
                    'lot_size': fetched_lot_size,
                    'current_price': 0.00
                }
            )

            if created:
                new_stocks_count += 1

        logger.info(f"Initial stock data population finished. Added {new_stocks_count} new stocks.")

        MoexDataService.update_stock_prices()

    @staticmethod
    @transaction.atomic
    def update_stock_prices():
        """Обновляет текущие цены (last) и размер лота (lotsize)."""
        tracked_tickers = set(Stock.objects.values_list('ticker', flat=True))
        stocks_to_update = []
        now = timezone.now()

        try:
            market = Market('shares', 'tqbr')
            market_data_list = market.marketdata()

            for data_row in market_data_list:
                # Все ключи в нижнем регистре: 'ticker', 'last', 'lotsize'
                ticker_symbol = data_row.get('ticker', None)
                if ticker_symbol:
                    ticker_symbol = ticker_symbol.upper()

                if ticker_symbol not in tracked_tickers:
                    continue

                last_price = data_row.get('last', None)
                lot_size = data_row.get('lotsize', None)
                stock = Stock.objects.get(ticker=ticker_symbol)
                has_changed = False

                if last_price and last_price > Decimal('0'):
                    if stock.current_price != last_price:
                        stock.current_price = last_price
                        has_changed = True

                # Обновляем лот, если он предоставлен API
                if lot_size is not None and lot_size > 0:
                    if stock.current_price != last_price:
                        stock.current_price = last_price
                        has_changed = True

                if has_changed:
                    stock.updated_at = now
                    stocks_to_update.append(stock)
            # ... (bulk_update logic) ...
            if stocks_to_update:
                # Обновляем и цену, и размер лота
                Stock.objects.bulk_update(stocks_to_update, ['current_price', 'lot_size', 'updated_at'])
                logger.info(f"Successfully updated prices for {len(stocks_to_update)} stocks.")
            else:
                logger.warning("No valid price updates received from MOEX.")

        except Exception as e:
            logger.error(f"Fatal error during MOEX price update: {e}")

