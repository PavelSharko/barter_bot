from initApp.config_loader import config
from repository.google_drive_manager import upload_db_folder
from services.keyboards.creator_inline_keyboards import get_menu_keyboard_for_developer
from services.msgs_utils.deleter_messages import clear_messages
from services.state_bot.global_store import add_message, global_msg_fast


async def save_actual_data(bot, user_id):
    msg = await bot.send_message(
        chat_id=config.DEVELOPER_CHAT_ID,
        text="📥 начинаю запись текущих данных  бота в гугл хранилище"
    )
    add_message(global_msg_fast, user_id, msg)
    succes = await upload_db_folder()
    await clear_messages(user_id, global_msg_fast)
    if succes:
        msg = await bot.send_message(
            chat_id=config.DEVELOPER_CHAT_ID,
            text="📥 все файлы успешно записаны",
            reply_markup=get_menu_keyboard_for_developer()
        )
        add_message(global_msg_fast, user_id, msg)
    else:
        msg = await bot.send_message(
            chat_id=config.DEVELOPER_CHAT_ID,
            text="📥 ошибка 🥲 -не записалось - копируй в резерв вручную все файлы на сервере перед остановкой бота",
            reply_markup=get_menu_keyboard_for_developer()
        )
        add_message(global_msg_fast, user_id, msg)
    return