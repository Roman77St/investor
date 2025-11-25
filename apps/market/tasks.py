from config import celery_app
from .services import MoexDataService
import logging

logger = logging.getLogger(__name__)

# Декоратор @celery_app.task превращает функцию в задачу, которую Celery может выполнять
@celery_app.task
def update_stock_prices_task():
    """Celery-задача для регулярного обновления цен акций."""
    logger.info("Executing periodic stock price update task...")
    try:
        # Вызываем нашу рабочую функцию из сервиса
        MoexDataService.update_stock_prices()
        logger.info("Stock price update task completed successfully.")
    except Exception as e:
        logger.error(f"Stock price update task failed: {e}")