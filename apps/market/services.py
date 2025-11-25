from decimal import Decimal
from moexalgo import Market, Ticker
from django.db import transaction
from .models import Stock
import logging

logger = logging.getLogger(__name__)


BLUE_CHIPS_TICKERS = [
    'SBER', 'GAZP', 'LKOH', 'TATN', 'T', 'NVTK', 'YDEX', 'GMKN',
    'PLZL', 'X5', 'ROSN', 'SNGS', 'MOEX', 'CHMF', 'NLMK'
]

class MoexDataService:

    @staticmethod
    def initialize_top_stocks():
        """Инициализирует базу данных основными акциями, получает их реальные имена."""
        logger.info("Starting initial stock data population...")
        new_stocks_count = 0

        try:
            market = Market('shares', 'tqbr')
            # 1. Получаем все метаданные ценных бумаг с доски TQBR
            security_list = market.tickers('*')

            # 2. Создаем словарь для быстрого поиска по тикеру (используем lowercase 'ticker')
            security_lookup = {
                s['ticker'].upper(): s for s in security_list
                if isinstance(s, dict) and s.get('ticker')
            }

        except Exception as e:
            logger.error(f"FATAL: Could not fetch security list via Market.tickers(): {e}")
            security_lookup = {}

        for ticker_symbol in BLUE_CHIPS_TICKERS:
            real_name = f"Компания {ticker_symbol}"
            fetched_lot_size = 1

            # 3. Ищем название и лот
            if sec_info := security_lookup.get(ticker_symbol):
                # Используем ключи ''shortname' и 'lotsize'
                if name_val := sec_info.get('shortname'):
                    real_name = name_val

                if lot_size_val := sec_info.get('lotsize'):
                    fetched_lot_size = lot_size_val

            # 4. Используем get_or_create
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

        # ... (проверки и логирование) ...

        try:
            market = Market('shares', 'tqbr')
            # Используем market.marketdata()
            market_data_list = market.marketdata()

            stocks_to_update = []

            for data_row in market_data_list:
                # Все ключи в нижнем регистре: 'ticker', 'last', 'lotsize'
                ticker_symbol = data_row.get('ticker', None)
                if ticker_symbol:
                    ticker_symbol = ticker_symbol.upper()

                if ticker_symbol not in tracked_tickers:
                    continue

                last_price = data_row.get('last', None)
                lot_size = data_row.get('lotsize', None)

                if last_price and last_price > Decimal('0'):
                    stock = Stock.objects.get(ticker=ticker_symbol)
                    stock.current_price = last_price

                    # Обновляем лот, если он предоставлен API
                    if lot_size is not None and lot_size > 0:
                        stock.lot_size = lot_size

                    stocks_to_update.append(stock)

            # ... (bulk_update logic) ...
            if stocks_to_update:
                # Обновляем и цену, и размер лота
                Stock.objects.bulk_update(stocks_to_update, ['current_price', 'lot_size'])
                logger.info(f"Successfully updated prices for {len(stocks_to_update)} stocks.")
            else:
                logger.warning("No valid price updates received from MOEX.")

        except Exception as e:
            logger.error(f"Fatal error during MOEX price update: {e}")