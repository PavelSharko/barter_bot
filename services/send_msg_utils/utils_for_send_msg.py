# utils_for_send_msg.py

import asyncio
import html
import logging
import re

from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramRetryAfter

from initApp.config_loader import config
from loggingConfig.colorFormatter import RED, MAGENTA, RESET, GREEN, YELLOW


"""
Вспомогательные утилиты для безопасной и надёжной отправки сообщений в Telegram-боте.
Основной смысл файла:
- Содержит методы для отправки сообщений с повторными попытками (retry), обработкой FloodWait (ограничений Telegram),
  а также для экранирования текста под разные режимы форматирования (Markdown, HTML).
- Помогает избежать блокировки или потери сообщений при рассылках и массовых отправках,
  автоматически выдерживает паузы и правильно реагирует на ошибки Telegram API.
"""

async def send_message_with_retries(bot, user_id, part, reply_markup=None):
    # todo этот метод полезен при рассылках
    try:
        part = str(part)
    except Exception as e:
        logging.error(f"❌ Невозможно привести part к строке: {repr(part)} — {e}")
        return False

    max_retries = 5
    retry_delay = 1    # секунд между попытками
    long_pause = 2     # пауза после всех попыток

    for attempt in range(1, max_retries + 1):
        try:
            kwargs = dict(
                chat_id=user_id,
                text=part,
                disable_web_page_preview=True,
                parse_mode=ParseMode.HTML,
            )

            # если есть клавиатура — добавляем ЭТО НАДО ДЛЯ ЧАТА ОЛЕРТОВ И ОБУЧЕНИ
            if reply_markup is not None:
                kwargs["reply_markup"] = reply_markup

            await bot.send_message(**kwargs)
            await asyncio.sleep(config.PAUSE_BEETWEN_RETRY_SEND_MSG)

            logging.debug(f"{GREEN}Сообщение успешно отправлено на попытке {attempt}{RESET}.")
            await asyncio.sleep(5)  # задержка после успешной отправки
            return True

        except TelegramRetryAfter as e:  # это аналог FloodWait
            wait_time = e.retry_after + 1
            logging.warning(f"🌊{MAGENTA} ПОЙМАЛИ FLOOD_WAIT: Ждём {wait_time} сек...{RESET}")
            await asyncio.sleep(wait_time)

        except Exception as e:
            logging.error(f"{RED}Ошибка при отправке сообщения на попытке {attempt}: {e}{RESET}")
            if attempt < max_retries:
                logging.warning(f"{YELLOW}Повторная попытка через {retry_delay} сек...{RESET}")
                await asyncio.sleep(retry_delay)
            else:
                logging.error(f"{RED}Не удалось отправить сообщение после {max_retries} попыток. Пауза {long_pause} сек.{RESET}")
                await asyncio.sleep(long_pause)

    return False  # 🔥 Не удалось



