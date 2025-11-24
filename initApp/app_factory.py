# app_factory.py
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from aiohttp import ClientTimeout
from initApp.config_loader import config



def create_app_and_handler():
    """
        Создаёт и настраивает Telegram-бота и диспетчер для обработки его сообщений.

        Возвращает:
            tuple: Кортеж из:
                - bot (Bot): Экземпляр бота с токеном из конфигурационного файла config.py.
                - dp (Dispatcher): Диспетчер для обработки событий бота.

        Важно:
            - Токен бота (BOT_TOKEN) нужно получить у BotFather в Telegram и прописать в config.py, например:
              BOT_TOKEN = "ваш_токен_здесь"
            - Используется in-memory storage для хранения состояния пользователей.
            - Таймаут для запросов берётся из config.TIMEOUT_RECONECT_BOT.
            - По умолчанию парсинг сообщений настроен на HTML.
        """
    storage = MemoryStorage()
    timeout = ClientTimeout(total=config.TIMEOUT_RECONECT_BOT)

    bot = Bot(token=config.BOT_TOKEN,
              default=DefaultBotProperties(parse_mode="HTML"),
              timeout=timeout)
    dp = Dispatcher(bot=bot, storage=storage)

    return bot, dp