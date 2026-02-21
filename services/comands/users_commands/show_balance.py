from aiogram import Bot
from aiogram.types import Message, CallbackQuery

from entity.Enums_entity import UserMetrics
from services.users_utils.all_users_manager import load_all_users
from services.state_bot.global_store import add_message, global_msg_fast

async def show_user_balance(call: CallbackQuery, bot: Bot):
    """
    Показывает баланс пользователя.
    """
    user_id = call.from_user.id
    users = load_all_users()
    
    balance = 0
    if user_id in users:
        balance = users[user_id].get(UserMetrics.BALANCE.value, 0)
        
    msg = await call.message.answer(
        f"💰 Ваш баланс: **{balance}** монет",
        parse_mode="Markdown",
        reply_markup=get_inline_keyboard_close()
    )
    add_message(global_msg_fast, user_id, msg)
    await call.answer()
