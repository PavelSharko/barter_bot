from aiogram import Bot
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from services.keyboards.bot_all_buttons import EditProfileButtons
from services.state_bot.global_store import add_message, global_msg_fast
from services.keyboards.sustem_inline_keyboard import get_inline_keyboard_close

async def handle_edit_profile_callbacks(bot: Bot, call: CallbackQuery, state: FSMContext):
    """
    Обработчик кнопок редактирования профиля (заглушка).
    """
    user_id = call.from_user.id
    data = call.data

    # Тут будет логика для каждой кнопки
    # Пока просто заглушка для всех кнопок из EditProfileButtons
    
    await call.answer()
    
    # Пытаемся найти человекочитаемое название кнопки
    try:
        button_name = next(item.value for item in EditProfileButtons if item.name.lower() == data)
    except StopIteration:
        button_name = data

    msg = await call.message.answer(
        f"Поймали колбек: {button_name} ({data})",
        reply_markup=get_inline_keyboard_close()
    )
    add_message(global_msg_fast, user_id, msg)
