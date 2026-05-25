from aiogram import Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from entity.Enums_entity import UserMetrics, UserProfileFields
from initApp.config_loader import config
from services.users_utils.all_users_manager import load_all_users, save_all_users
from services.users_utils.user_profile_manager import load_profiles
from services.keyboards.bot_all_buttons import ModeratorChatButtons
from services.keyboards.creator_persistent_keyboards import get_cancel_keyboard, get_persistent_moderator_menu
from services.state_bot.global_store import add_message, global_msg_fast
from handlers.fsm_utils import set_waiting_input, check_cancel_input, clear_waiting_input
from services.users_utils.transactions_history_manager import add_transaction_log

async def start_send_coins_input(call: CallbackQuery, bot: Bot, state: FSMContext):
    """
    Start process of sending coins.
    Sets FSM state to wait for input: "user_id/name amount".
    """
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    
    await set_waiting_input(
        state, bot, chat_id, user_id,
        command_name=ModeratorChatButtons.SEND_COINS.name.lower(),
        timeout=config.TIME_TO_INPUT_MSG_FSM
    )
    
    msg = await call.message.answer(
        text="Введите ID пользователя или Имя из анкеты и сумму монет через пробел.\nПример: `123456789 50` или `Иван Иванов 50`",
        params={"parse_mode": "Markdown"},
        reply_markup=get_cancel_keyboard()
    )
    add_message(global_msg_fast, user_id, msg)
    await call.answer()


async def process_send_coins_input(message: Message, state: FSMContext, bot: Bot):
    """
    Process the input for sending coins.
    Expected format: "identifier amount"
    """
    user_id = message.from_user.id
    chat_id = message.chat.id

    # Check for cancel
    if await check_cancel_input(message.text, message, state):
        return

    text = message.text.strip()
    
    # Try to split by last space to separate amount
    parts = text.rsplit(" ", 1)

    if len(parts) < 2:
        msg = await message.answer("⚠️ Неверный формат. Введите ID/Имя и сумму через пробел.\nПример: `123456789 50`")
        add_message(global_msg_fast, user_id, msg)
        add_message(global_msg_fast, user_id, message)
        return

    identifier = parts[0].strip()
    amount_str = parts[1].strip()

    # Validate amount
    try:
        amount = int(amount_str)
    except ValueError:
        msg = await message.answer("⚠️ Сумма должна быть числом.")
        add_message(global_msg_fast, user_id, msg)
        add_message(global_msg_fast, user_id, message)
        return

    if not (1 <= amount <= 100):
        msg = await message.answer("⚠️ Сумма должна быть от 1 до 100.")
        add_message(global_msg_fast, user_id, msg)
        add_message(global_msg_fast, user_id, message)
        return

    # Load User Profiles to find target
    profiles = load_profiles()
    
    target_user_id = None
    
    # Check by ID (key)
    # Profiles dict from load_profiles() has INT keys.
    if identifier.isdigit() and int(identifier) in profiles:
        target_user_id = identifier
    else:
        # Check by name in values
        identifier_lower = identifier.casefold()
        for uid, data in profiles.items():
            name = data.get(UserProfileFields.NAME.value)
            if name and name.casefold() == identifier_lower:
                target_user_id = str(uid)
                break
    
    if not target_user_id:
        msg = await message.answer(f"❌ Пользователь `{identifier}` не найден (ни по ID, ни по имени в анкете).", parse_mode="Markdown")
        add_message(global_msg_fast, user_id, msg)
        add_message(global_msg_fast, user_id, message)
        return

    # Update Balance in All Users
    users = load_all_users()
    
    # Ensure target_user_id is in users map (it should be if they have profile, but logic might differ)
    # Check string vs int key
    final_key = None
    if target_user_id in users:
        final_key = target_user_id
    elif int(target_user_id) in users:
        # If stored as int keys (unlikely for JSON load but possible in python dict if constructed so)
        # Usually JSON keys are str.
        # But let's check string conversion
        pass 
    
    # Users dict has INT keys (see load_all_users implementation)
    try:
        final_key = int(target_user_id)
    except ValueError:
         msg = await message.answer(f"⚠️ Ошибка формата ID пользователя: {target_user_id}")
         add_message(global_msg_fast, user_id, msg)
         add_message(global_msg_fast, user_id, message)
         return
    
    if final_key not in users:
         # Should not happen if profile exists, but safety check
         msg = await message.answer(f"⚠️ Профиль найден, но основной записи пользователя {target_user_id} нет.")
         add_message(global_msg_fast, user_id, msg)
         add_message(global_msg_fast, user_id, message)
         return

    # --- Check Moderator Balance ---
    moderator_id = user_id  # The one executing the command
    
    if moderator_id not in users:
        # Should catch weird edge cases
        msg = await message.answer("⚠️ Вы не найдены в базе пользователей. Невозможно списать монеты.")
        add_message(global_msg_fast, user_id, msg)
        add_message(global_msg_fast, user_id, message)
        return

    moderator_balance = users[moderator_id].get(UserMetrics.BALANCE.value, 0)
    
    if moderator_balance < amount:
        msg = await message.answer(f"⚠️ У вас недостаточно монет!\nВаш баланс: **{moderator_balance}**\nТребуется: **{amount}**", parse_mode="Markdown")
        add_message(global_msg_fast, user_id, msg)
        add_message(global_msg_fast, user_id, message)
        return

    # --- Execute Transaction ---
    # Deduct from Moderator
    users[moderator_id][UserMetrics.BALANCE.value] = moderator_balance - amount
    
    # Add to User
    user_balance = users[final_key].get(UserMetrics.BALANCE.value, 0)
    new_user_balance = user_balance + amount
    users[final_key][UserMetrics.BALANCE.value] = new_user_balance
    
    save_all_users()

    # Записываем в отдельный лог транзакций
    add_transaction_log(
        sender_id=moderator_id, 
        receiver_id=final_key, 
        amount=amount, 
        description="Перевод монет от модератора"
    )

    # Notify Moderator
    success_msg = await message.answer(
        f"✅ Перевод выполнен!\n"
        f"Кому: `{identifier}` (ID: `{target_user_id}`)\n"
        f"Сумма: **{amount}**\n"
        f"Ваш новый баланс: **{users[moderator_id][UserMetrics.BALANCE.value]}**",
        parse_mode="Markdown", reply_markup=get_persistent_moderator_menu()
    )
    add_message(global_msg_fast, user_id, message) # Только удаляем исходное сообщение с суммой, алерт оставляем

    # Notify Developer
    try:
        await bot.send_message(
            chat_id=config.DEVELOPER_CHAT_ID,
            text=f"💸 **ВНИМАНИЕ: ПЕРЕВОД ОТ МОДЕРАТОРА**\n"
                 f"Модератор (ID: {moderator_id}) перевел **{amount}** 🪙 пользователю `{identifier}` (ID: {target_user_id}).\n"
                 f"Новый баланс модератора: {users[moderator_id][UserMetrics.BALANCE.value]}",
            parse_mode="Markdown"
        )
    except Exception as e:
        import logging
        logging.error(f"Failed to send transfer alert to developer: {e}")

    # Notify User
    try:
        await bot.send_message(
            chat_id=int(target_user_id),
            text=(
                f"🎁 **Вам начислено {amount} монет!**\n"
                f"Ваш текущий баланс: **{new_user_balance}**"
            ),
            parse_mode="Markdown"
        )
    except Exception:
        # User might have blocked bot
        pass

    # Clear state
    await clear_waiting_input(state, chat_id, user_id)
