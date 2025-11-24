# logging_config.py
import asyncio
import logging

from initApp.config_loader import config
from loggingConfig.AsyncTelegramHandler import AsyncTelegramHandler
from loggingConfig.colorFormatter import ColorFormatter


"""
Настройка логирования для проекта с поддержкой цветного вывода в консоль
и отправкой ошибок в Telegram.

Функция setup_logging принимает уровень логирования и объект бота (app),
настраивает корневой логгер:

- Очищает старые обработчики, если они есть.
- Добавляет StreamHandler с кастомным ColorFormatter для цветного отображения логов в консоли.
- Добавляет AsyncTelegramHandler — асинхронный обработчик, отправляющий ошибки в Telegram.

Функция get_log_level позволяет получить уровень логирования по имени (строке),
поддерживает стандартные уровни (DEBUG, INFO, WARNING, ERROR, CRITICAL).

Такой централизованный подход к логированию гарантирует единообразный вывод логов,
гибкую настройку уровней и быструю реакцию на ошибки через Telegram-уведомления.
"""
def setup_logging(level, app):
    # todo
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Удаляем старые обработчики, если есть
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    handler = logging.StreamHandler()
    fmt = '[%(asctime)s] %(levelname)s: %(message)s'
    datefmt = '%Y-%m-%d %H:%M:%S'
    handler.setFormatter(ColorFormatter(fmt=fmt, datefmt=datefmt))

    root_logger.addHandler(handler)

    telegram_handler = AsyncTelegramHandler(app, config.DEVELOPER_CHAT_ID, loop=asyncio.get_event_loop())
    telegram_handler.setFormatter(ColorFormatter(fmt=fmt, datefmt=datefmt))
    root_logger.addHandler(telegram_handler)

def get_log_level(level_name):
    level_name = level_name.upper()
    levels = {
        "CRITICAL": logging.CRITICAL,
        "ERROR": logging.ERROR,
        "WARNING": logging.WARNING,
        "INFO": logging.INFO,
        "DEBUG": logging.DEBUG,
        "NOTSET": logging.NOTSET,
    }
    return levels.get(level_name, logging.INFO)