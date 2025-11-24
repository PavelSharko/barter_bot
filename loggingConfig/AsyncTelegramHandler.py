# loggingConfig/AsyncTelegramHandler.py

import logging
import asyncio
from services.msgs.utils_for_send_msg import escape_markdown

"""
Модуль логгирования с асинхронной отправкой ошибок в Telegram.

Класс AsyncTelegramHandler расширяет стандартный logging.Handler,
чтобы асинхронно отправлять сообщения об ошибках из лога напрямую в указанный чат Telegram.

Основные возможности:
- Принимает записи логов уровня ERROR и выше.
- Использует очередь asyncio.Queue для неблокирующей отправки сообщений.
- Сообщения форматируются и, если слишком длинные, автоматически обрезаются.
- Отправка сообщений происходит асинхронно в фоне, с небольшой задержкой между отправками.
- Позволяет быстро получать уведомления о критических ошибках в режиме реального времени.

Использование данного обработчика позволяет эффективно следить за ошибками бота через Telegram,
без блокировки основного приложения.

"""

class AsyncTelegramHandler(logging.Handler):
    def __init__(self, app, target_chat, loop=None):
        super().__init__(level=logging.ERROR)
        self.app = app
        self.target_chat = target_chat
        self.loop = loop or asyncio.get_event_loop()
        self.queue = asyncio.Queue()
        self.loop.create_task(self._send_from_queue())

    def emit(self, record):
        try:
            msg = self.format(record)
            self.queue.put_nowait(msg)
        except Exception:
            self.handleError(record)

    async def _send_from_queue(self):
        # ⬇️ импорт внутри, только когда реально нужен
        from initApp.config_loader import config

        while True:
            msg = await self.queue.get()
            msg_escaped = escape_markdown(msg)

            MAX_LEN = 1000
            if len(msg_escaped) > MAX_LEN:
                msg_escaped = msg_escaped[:MAX_LEN] + "\n...[truncated]"

            try:
                await self.app.send_message(
                    config.DEVELOPER_CHAT_ID,
                    f"❗️*Ошибка в логе бота {config.NAME_BOT}:*\n``````{msg_escaped}"
                )
            except Exception as e:
                logging.getLogger(__name__).warning(f"Ошибка при отправке лога в Telegram: {e}")

            await asyncio.sleep(2)