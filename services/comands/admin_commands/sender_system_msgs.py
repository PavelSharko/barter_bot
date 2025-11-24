import asyncio
import logging
from initApp.config_loader import config
from loggingConfig.colorFormatter import GREEN, RESET
from services.keyboards.creator_inline_keyboards import get_menu_keyboard_for_developer


async def send_startup_message(bot):
    await asyncio.sleep(2)  # ждём, пока бот подключится

    await bot.send_message(
        chat_id=config.DEVELOPER_CHAT_ID,
        text=f"🚀 @{config.NAME_BOT} запущен!\n\nверсия {config.VERSION_REALISE}\n\n",
        reply_markup=get_menu_keyboard_for_developer()
    )

    logging.warning(f"🚀 {GREEN} @{config.NAME_BOT} запущен!\n\nверсия {config.VERSION_REALISE} {RESET}\n\n")
