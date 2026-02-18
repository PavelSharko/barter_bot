from aiogram import Bot
from aiogram.types import Message, CallbackQuery

from entity.Enums_entity import UserLifecycleStatus, UserFields
from initApp.config_loader import config
from services.users_utils.all_users_manager import load_all_users
from services.state_bot.global_store import add_message, global_msg_fast

async def check_blocked_user(user_id: int, bot: Bot, event: Message | CallbackQuery) -> bool:
    """
    Проверяет, заблокирован ли пользователь.
    Если заблокирован:
      - Отправляет сообщение (или answer для callback) о блокировке с причиной.
      - Возвращает True.
    Если не заблокирован:
      - Возвращает False.
    """
    users = load_all_users()
    
    # Если пользователя нет в базе - он не может быть заблокирован (или он новый)
    if user_id not in users:
        return False

    user_data = users[user_id]
    status = user_data.get(UserFields.STATUS.value)

    if status == UserLifecycleStatus.BLOCKED.value:
        reason = user_data.get(UserFields.REASON_FOR_BLOCKING_USER.value, "Причина не указана")
        
        text = (
            f"🚫 **Вы заблокированы!**\n\n"
            f"**Причина:** {reason}\n\n"
            f"По правилам клуба вы заблокированы. Если вы считаете, что это ошибка, "
            f"обратитесь к модератору: ID {config.MODERATOR_CONTACT_ID}"
        )

        try:
            if isinstance(event, CallbackQuery):
                await event.answer("🚫 Вы заблокированы!", show_alert=True)
                msg = await event.message.answer(text, parse_mode="Markdown")
                add_message(global_msg_fast, user_id, msg)
            elif isinstance(event, Message):
                msg = await event.answer(text, parse_mode="Markdown")
                add_message(global_msg_fast, user_id, msg)
                # Если это было текстовое сообщение пользователя, его тоже можно добавить в пул для очистки,
                # но обычно глобальный стор чистится при переходах. 
                # Тут можно добавить само сообщение юзера, чтобы оно потом удалилось
                add_message(global_msg_fast, user_id, event) 
        except Exception:
            pass
            
        return True

    return False
