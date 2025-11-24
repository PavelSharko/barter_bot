import asyncio
from aiogram.exceptions import TelegramRetryAfter, TelegramNetworkError

async def safe_send_message(bot, chat_id: int, text: str, reply_markup=None, retry: int = 3, delay: int = 2):
    """
    Отправка сообщения с ретраем (повтор через delay сек).
    """
    for attempt in range(1, retry + 1):
        try:
            return await bot.send_message(
                chat_id=chat_id,
                text=text,
                reply_markup=reply_markup
            )
        except (TelegramRetryAfter, TelegramNetworkError) as e:
            if attempt == retry:
                raise
            await asyncio.sleep(delay)
        except Exception as e:
            if attempt == retry:
                raise
            await asyncio.sleep(delay)