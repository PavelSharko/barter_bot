from aiogram import Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from entity.Enums_entity import UserLifecycleStatus, UserFields
from initApp.config_loader import config
from services.msgs_utils.deleter_messages import clear_messages
from services.users_utils.all_users_manager import load_all_users, save_all_users
from services.users_utils.blocking_manager import blocking_manager
from services.keyboards.bot_all_buttons import ModeratorChatButtons
from services.keyboards.creator_persistent_keyboards import get_cancel_keyboard, get_persistent_moderator_menu
from services.state_bot.global_store import add_message, global_msg_fast
from handlers.fsm_utils import set_waiting_input, check_cancel_input, clear_waiting_input

async def start_exclude_participant_input(call: CallbackQuery, bot: Bot, state: FSMContext):
    """
    Start process of excluding a participant.
    Sets FSM state to wait for input: "user_id reason".
    """
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    
    await set_waiting_input(
        state, bot, chat_id, user_id,
        command_name=ModeratorChatButtons.EXCLUDE_PARTICIPANT.name.lower(),
        timeout=config.TIME_TO_INPUT_MSG_FSM
    )
    
    msg = await call.message.answer(
        text="Введите ID пользователя и причину блокировки через пробел.\nПример: `123456789 Спам и мошенничество`",
        params={"parse_mode": "Markdown"},
        reply_markup=get_cancel_keyboard()
    )
    add_message(global_msg_fast, user_id, msg)
    await call.answer()


async def process_exclude_participant_input(message: Message, state: FSMContext, bot: Bot):
    """
    Process the input for excluding a participant.
    Expected format: "user_id reason"
    """
    user_id = message.from_user.id
    chat_id = message.chat.id

    # Check for cancel
    if await check_cancel_input(message.text, message, state):
        await clear_messages(user_id, global_msg_fast)
        return

    text = message.text.strip()
    parts = text.split(" ", 1) # Split only once

    if len(parts) < 2:
        msg = await message.answer("⚠️ Неверный формат. Введите ID и причину через пробел.\nПример: `123456789 Спам`")
        add_message(global_msg_fast, user_id, msg)
        add_message(global_msg_fast, user_id, message)
        return

    try:
        target_user_id_str = parts[0].strip()
        target_user_id = int(target_user_id_str)
        reason = parts[1].strip()
    except ValueError:
        msg = await message.answer("⚠️ ID пользователя должен быть числом.")
        add_message(global_msg_fast, user_id, msg)
        add_message(global_msg_fast, user_id, message)
        return

    if len(reason) < 5:
         msg = await message.answer("⚠️ Причина слишком короткая. Минимум 5 символов.")
         add_message(global_msg_fast, user_id, msg)
         add_message(global_msg_fast, user_id, message)
         return

    users = load_all_users()
    
    # Check if user exists (check both int and str keys just in case, though load_all_users should be consistent)
    # The JSON keys are usually strings, but we cast to int for logic. 
    # Let's ensure we check against string keys if that's how they are stored.
    # Based on previous code, keys seem to be stored as strings in JSON but we might use int in logic.
    # Safe check:
    found = False
    if target_user_id in users:
        found = True
    elif str(target_user_id) in users:
        target_user_id = str(target_user_id)
        found = True
        
    if not found:
        msg = await message.answer(f"❌ Пользователь с ID {target_user_id} не найден в базе.")
        add_message(global_msg_fast, user_id, msg)
        add_message(global_msg_fast, user_id, message)
        return

    # Check already blocked
    current_status = users[target_user_id].get(UserFields.STATUS.value)
    if current_status == UserLifecycleStatus.BLOCKED.value:
        msg = await message.answer(f"⚠️ Пользователь {target_user_id} уже заблокирован.")
        add_message(global_msg_fast, user_id, msg)
        add_message(global_msg_fast, user_id, message)
        # We allow to update reason? Or just stop? User asked to "validate that id exists", not specifically check status,
        # but logic implies we are changing status.
        # Let's update the block reason and log it anyway as a re-block/update.
        # But commonly we might want to just stop. 
        # Requirement: "validate to verify id and reason mandatory".
        # Let's proceed to update status (idempotent) and log new reason.

    # Execute Block
    users[target_user_id][UserFields.STATUS.value] = UserLifecycleStatus.BLOCKED.value
    users[target_user_id][UserFields.REASON_FOR_BLOCKING_USER.value] = reason
    save_all_users()

    # Log to BlockingManager
    block_id = blocking_manager.add_block_record(
        user_id=int(target_user_id),
        moderator_id=user_id,
        reason=reason,
        status_before=current_status if current_status else "unknown",
        status_after=UserLifecycleStatus.BLOCKED.value
    )

    # Notify User
    try:
        await bot.send_message(
            chat_id=int(target_user_id),
            text=(
                f"🚫 **ВАШ АККАУНТ ЗАБЛОКИРОВАН**\n"
                f"Причина: {reason}\n\n"
                f"Для обжалования свяжитесь с [администратором](tg://user?id={config.MODERATOR_CONTACT_ID})."
            ),
            parse_mode="Markdown"
        )
    except Exception as e:
        # User might have blocked bot
        pass

    # Notify Admin
    success_msg = await message.answer(
        f"✅ Пользователь `{target_user_id}` успешно заблокирован.\n"
        f"Причина: {reason}\n"
        f"ID блокировки: `{block_id}`",
        parse_mode="Markdown", reply_markup=get_persistent_moderator_menu()
    )
    add_message(global_msg_fast, user_id, message) # Remove input message too?

    # Clear state
    await clear_waiting_input(state, chat_id, user_id)
