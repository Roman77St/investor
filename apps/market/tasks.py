from config import celery_app
from .services import MoexDataService
import logging

logger = logging.getLogger(__name__)

# Декоратор @celery_app.task превращает функцию в задачу, которую Celery может выполнять
@celery_app.task
def update_stock_prices_task():
    """Celery-задача для регулярного обновления цен акций."""
    logger.info("Выполнение задачи периодического обновления цен...")
    try:
        # Вызываем нашу рабочую функцию из сервиса
        MoexDataService.update_stock_prices()
        logger.info("Stock price update task completed successfully.")
    except Exception as e:
        logger.error(f"Stock price update task failed: {e}")

@celery_app.task
def initialize_all_stocks_task():
    """
    Celery задача для полной инициализации акций (запускается при необходимости).
    """
    logger.info("Celery Beat: Начинаю инициализацию всех акций TQBR.")
    try:
        MoexDataService.initialize_top_stocks()
        logger.info("Celery Beat: Инициализация акций завершена.")
    except Exception as e:
        logger.error(f"Celery Beat: Ошибка при инициализации акций: {e}")