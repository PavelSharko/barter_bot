# План по улучшению обработки ошибок (Глобальный перехватчик)

## Проблема:
Текущая обработка ошибок через блоки `try/except` во многих обработчиках кнопок и команд скрывает причину ошибки от пользователя и разработчика, а так же ведет к разрозненности кода. Когда бот падает на CallbackQuery или Message (например: "Ошибка при обработке кнопки"), разработчик не получает сразу уведомление в Telegram с трейсом.

## Решение: Создание глобального Error Handler (aiogram v3)
В aiogram есть возможность отлавливать все необработанные ошибки (Exceptions) на уровне диспетчера в одном месте. 

### Шаг 1: Создание обработчика событий ошибок
Создать новый файл `handlers/error_handler.py`:
```python
import logging
import traceback
from aiogram import Router
from aiogram.types import ErrorEvent
from services.send_msg_utils.utuls_send_msg import safe_send_message
from initApp.config_loader import config

error_router = Router()

@error_router.errors()
async def global_error_handler(event: ErrorEvent, bot):
    # Получаем саму ошибку и стек трейс
    exception = event.exception
    traceback_str = traceback.format_exc()
    
    # 1. Логируем ошибку локально (например в консоль/файл)
    logging.error(f"Глобальная ошибка вызванная из update {event.update.update_id}: \n{traceback_str}")
    
    # 2. Уведомляем пользователя (если возможно)
    user_msg = "⚠️ Я сломался, давай еще разок! Попробуйте вызвать команду заново или вернитесь в главное меню."
    try:
        # Пробуем достать чат айди из апдейта
        bot_user_id = None
        if event.update.callback_query:
            bot_user_id = event.update.callback_query.from_user.id
            await event.update.callback_query.answer() # Закрываем часики
        elif event.update.message:
            bot_user_id = event.update.message.chat.id
            
        if bot_user_id:
            await safe_send_message(bot, chat_id=bot_user_id, text=user_msg)
    except Exception as e:
        logging.error(f"Не смогли отправить извинения пользователю: {e}")

    # 3. Отправляем алерт разработчику в DEVELOPER_CHAT_ID!
    alert_text = (
        f"🚨 <b>КРИТИЧЕСКАЯ ФАТАЛЬНАЯ ОШИБКА БОТА</b>\n\n"
        f"<b>Ошибка:</b> <code>{type(exception).__name__}: {str(exception)}</code>\n\n"
        f"<b>Трейс:</b>\n<pre>{traceback_str[-3000:]}</pre>" # Обрезаем трейс чтобы влез в лимиты тг
    )
    
    await safe_send_message(
        bot, 
        chat_id=config.DEVELOPER_CHAT_ID, 
        text=alert_text, 
        parse_mode="HTML"
    )
```

### Шаг 2: Регистрация роутера
В главном файле `barter_bot.py` необходимо подключить этот роутер к корневому диспетчеру (там же, где мы регистрируем `message_handlers.router` и прочие).
```python
from handlers.error_handler import error_router
# ...
dp.include_router(error_router)
```

### Шаг 3: Чистка старых try-except
Затем мы можем убрать `try-except Exception` в конкретных хендлерах (например: выводящих `print("Ошибка при обработке кнопки")`), так как теперь любая авария будет перехвачена глобальным ловцом `global_error_handler`. Бот не упадет (потому что ошибка перехвачена), выдаст пользователю "Я сломался", а админу — подробный трейсбэк с причиной.
