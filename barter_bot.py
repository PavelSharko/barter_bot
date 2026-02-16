import asyncio
import logging
import sys

from handlers import message_handlers
from initApp.app_factory import create_app_and_handler
from initApp.background import start_background_tasks
from initApp.config_loader import config, get_stend
from services.state_bot import global_store

bot, dp = create_app_and_handler()

# Регистрируем хэндлеры
message_handlers.register_handlers(dp, bot)
global_store.bot = bot


if __name__ == "__main__":# logger = logging.getLogger(__name__) - как сделать???
    loop = asyncio.get_event_loop()

    # --- Логирование ---
    if len(sys.argv) > 1:
        level = getattr(logging, sys.argv[1].upper(), logging.INFO)
    else:
        level = logging.INFO

    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s]: %(message)s"
    )

    loop.create_task(start_background_tasks(loop, bot))

    logging.warning(f"БОТ ЗАПУЩЕН: STEND={get_stend()}, версия {config.VERSION_REALISE}")
    try:
        loop.run_until_complete(dp.start_polling(bot))
    except KeyboardInterrupt:
        logging.warning("БОТ остановлен вручную:")


