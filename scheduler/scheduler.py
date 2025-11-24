# scheduler.py
import asyncio
import logging

from initApp.config_loader import config
from loggingConfig.colorFormatter import YELLOW, RESET



async def set_scheduler(bot):
    while True:
        logging.debug(f" {YELLOW} start  scheduler {RESET}")
        # todo тут вызываются методы по расписанию бота
        await asyncio.sleep(config.SCHEDULER_INTERVAL_TO_SEND_LATER)


