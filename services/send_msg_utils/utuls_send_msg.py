import asyncio
import logging
from aiogram import Bot
from aiogram.exceptions import TelegramRetryAfter, TelegramNetworkError
from initApp.config_loader import config
from typing import Union

async def safe_send_message(bot: Bot, chat_id: Union[int, str], text: str, retry: int = 3, delay: int = 1, **kwargs):
    """
    Универсальная обертка над bot.send_message.
    Принимает любые параметры (parse_mode, reply_markup и т.д.) через **kwargs.
    Делает повторные попытки (ретраи) при ошибках сети или лимитах.
    Если отправить не удалось, логирует ошибку и шлет алерт в DEVELOPER_CHAT_ID.
    """
    last_error = None
    
    for attempt in range(1, retry + 1):
        try:
            return await bot.send_message(
                chat_id=chat_id,
                text=text,
                **kwargs
            )
        except TelegramRetryAfter as e:
            last_error = e
            logging.warning(f"Flood limit exceeded. Retrying in {e.retry_after} seconds... (Attempt {attempt}/{retry})")
            await asyncio.sleep(e.retry_after)
        except TelegramNetworkError as e:
            last_error = e
            logging.warning(f"Network error: {e}. Retrying in {delay} seconds... (Attempt {attempt}/{retry})")
            await asyncio.sleep(delay)
        except Exception as e:
            last_error = e
            # Для остальных ошибок (например, юзер заблокировал бота) нет смысла делать ретраи часто,
            # но можно сделать небольшую паузу и попробовать еще раз (на случай временных багов)
            logging.warning(f"Failed to send message: {e}. Retrying... (Attempt {attempt}/{retry})")
            await asyncio.sleep(delay)
            
    # Если мы дошли сюда, значит все попытки исчерпаны
    error_msg = f"Failed to send message to {chat_id} after {retry} attempts. Last error: {last_error}"
    logging.error(error_msg)
    
    # Отправляем алерт разработчику
    try:
        alert_text = (
            f"🚨 <b>ОШИБКА ОТПРАВКИ СООБЩЕНИЯ</b>\n"
            f"<b>Chat ID:</b> <code>{chat_id}</code>\n"
            f"<b>Error:</b> <code>{str(last_error)}</code>\n"
            f"<b>Text (preview):</b>\n{text[:200]}"
        )
        await bot.send_message(
            chat_id=config.DEVELOPER_CHAT_ID,
            text=alert_text,
            parse_mode="HTML"
        )
    except Exception as alert_e:
        logging.error(f"FATAL: Failed to send alert to developer: {alert_e}")
        
    return None