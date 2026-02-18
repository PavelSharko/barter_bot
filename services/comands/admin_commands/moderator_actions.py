from aiogram import Bot
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from entity.Enums_entity import UserFields, UserLifecycleStatus, UserMetrics
from initApp.config_loader import config
from services.keyboards.bot_all_buttons import ProfileRegistration_Menu, CommandsBot, AdminChatButtons, CategoryButtons
from services.keyboards.creator_persistent_keyboards import get_persistent_main_menu, get_cancel_keyboard
from services.keyboards.keyboards_for_registration import get_rejected_keyboard, get_category_keyboard
from services.msgs_utils.deleter_messages import clear_messages
from services.users_utils.all_users_manager import load_all_users, save_all_users
from services.state_bot.global_store import global_msg_fast, global_msg_for_close, add_message
from handlers.fsm_utils import set_waiting_input, check_cancel_input, clear_waiting_input



# Локальное хранилище для процесса отказа: {admin_id: {'user_id': int, 'message_id': int, 'text': str, 'is_caption': bool}}
rejection_targets: dict[int, dict] = {}

# Локальное хранилище для процесса принятия (выбора категории): {admin_id: {'user_id': int, 'message_id': int, 'text': str, 'is_caption': bool}}
acceptance_targets: dict[int, dict] = {}


async def handle_moderator_action(call: CallbackQuery, bot: Bot, state: FSMContext):
    """
    Обработка действий модератора (Принять/Отклонить заявку).
    Format callback_data: action_userid
    """
    try:
        data = call.data.split('_')
        action = data[0]
        user_id = int(data[1])
    except (IndexError, ValueError):
        await call.answer("Ошибка в данных кнопки", show_alert=True)
        return

    users = load_all_users()
    if user_id not in users:
        # Попытка найти по строковому ключу (на всякий случай)
        if str(user_id) in users:
            user_id = str(user_id)
        else:
            await call.answer("Пользователь не найден", show_alert=True)
            await call.message.edit_reply_markup(reply_markup=None)
            await call.message.edit_text(call.message.text + "\n\n❌ Пользователь не найден в базе")
            return
        
    # Определяем текст и тип сообщения (фото или текст)
    # Если есть caption - значит это медиа (фото/видео) с подписью
    msg_text = call.message.caption if call.message.caption else call.message.text
    is_caption = bool(call.message.caption)

    # Логика ПРИНЯТЬ
    if action == ProfileRegistration_Menu.ACCEPT.name.lower():
        # Сохраняем ID пользователя и ID сообщения, чтобы потом обновить его
        acceptance_targets[call.from_user.id] = {
            'user_id': int(user_id),
            'message_id': call.message.message_id,
            'text': msg_text or "",
            'is_caption': is_caption
        }
        
        # Отправляем клавиатуру выбора категории
        msg = await bot.send_message(
            chat_id=call.message.chat.id,
            text=f"✅ Выберите категорию для участника {user_id}:",
            reply_markup=get_category_keyboard()
        )
        
        # Добавляем сообщение в стор для закрытия (Global_msg_for_close)
        add_message(global_msg_for_close, int(user_id), msg)
        add_message(global_msg_fast, call.from_user.id, msg) # И в фаст тоже
        
        await call.answer("Выберите категорию ⬇️")

    # Логика ОТКЛОНИТЬ (Запрос причины)
    elif action == ProfileRegistration_Menu.REJECT.name.lower():
        await call.answer("Укажите причину отказа 📝")
        
        # Устанавливаем состояние ожидания ввода (сначала, так как оно делает clear)
        await set_waiting_input(
            state, bot, call.message.chat.id, call.from_user.id,
            command_name=ProfileRegistration_Menu.REJECT.name.lower(),
            timeout=config.TIME_TO_INPUT_MSG_FSM
        )

        # Сохраняем данные для отказа
        rejection_targets[call.from_user.id] = {
            'user_id': int(user_id),
            'message_id': call.message.message_id,
            'text': msg_text or "",
            'is_caption': is_caption
        }
        
        # Отправляем сообщение запроса
        msg = await bot.send_message(
            chat_id=call.message.chat.id,
            text=f"📝 Введите причину отказа для пользователя {user_id} (минимум 10 символов):",
            reply_markup=get_cancel_keyboard()
        )
        add_message(global_msg_fast, call.from_user.id, msg)


async def process_rejection_reason(message: Message, state: FSMContext, bot: Bot):
    """
    Обработка введенной причины отказа.
    """
    if await check_cancel_input(message.text, message, state):
        rejection_targets.pop(message.from_user.id, None)
        return

    reason = message.text or ""
    
    if len(reason) < 10:
        msg = await message.answer("⚠️ Причина слишком короткая. Минимум 10 символов.")
        add_message(global_msg_fast, message.from_user.id, msg)
        add_message(global_msg_fast, message.from_user.id, message)
        return

    # Получаем данные из локального словаря
    target_data = rejection_targets.get(message.from_user.id)
    
    if not target_data:
        await message.answer("❌ Ошибка: не найден ID (возможно, прошло много времени).")
        return

    target_user_id = target_data.get('user_id')
    origin_msg_id = target_data.get('message_id')
    origin_text = target_data.get('text', "")
    is_caption = target_data.get('is_caption', False)

    users = load_all_users()
    if target_user_id not in users:
        await message.answer("❌ Пользователь не найден в базе.")
        return

    # Проверка статуса...
    current_status = users[target_user_id].get(UserFields.STATUS.value)
    if current_status == UserLifecycleStatus.REJECTED.value:
         await message.answer(f"⚠️ Пользователь {target_user_id} уже был отклонен.")
         return

    # 1. Обновляем статус
    users[target_user_id][UserFields.STATUS.value] = UserLifecycleStatus.REJECTED.value
    users[target_user_id][UserFields.BLOCK_PROFILE_INFO_REASON.value] = reason
    save_all_users()
    
    rejection_targets.pop(message.from_user.id, None)

    # 2. Уведомляем пользователя
    await clear_messages(target_user_id, global_msg_fast)
    await clear_messages(config.MODERATOR_CONTACT_ID, global_msg_fast)
    try:
        msg = await bot.send_message(
            chat_id=target_user_id,
            text=f"🚫 **К сожалению, ваша заявка была отклонена модератором.**\n\nПричина: {reason}",
            parse_mode="Markdown",
            reply_markup=get_rejected_keyboard()
        )
        add_message(global_msg_fast, target_user_id, msg)
        await message.answer(f"✅ Пользователь {target_user_id} отклонен.\nПричина: {reason}")
    except Exception as e:
        await message.answer(f"✅ Пользователь отклонен, но не удалось уведомить: {e}")

    await clear_waiting_input(state, message.chat.id, message.from_user.id)
    
    # 3. Обновляем сообщение администратора (исходную заявку)
    if origin_msg_id:
        new_text = f"{origin_text}\n\n🚫 **ЗАЯВКА ОТКЛОНЕНА**\nПричина: {reason}"
        try:
            if is_caption:
                await bot.edit_message_caption(
                    chat_id=message.chat.id,
                    message_id=origin_msg_id,
                    caption=new_text,
                    reply_markup=None
                )
            else:
                await bot.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=origin_msg_id,
                    text=new_text,
                    reply_markup=None
                )
        except Exception:
            pass


async def handle_category_selection(call: CallbackQuery, bot: Bot):
    """
    Обработка выбора категории для принимаемого пользователя.
    Callback data: category_0, category_25 ...
    """
    admin_id = call.from_user.id
    target_data = acceptance_targets.get(admin_id)

    if not target_data:
        await call.answer("❌ Ошибка: не выбран пользователь.", show_alert=True)
        await call.message.delete()
        return

    target_user_id = target_data.get('user_id')
    origin_msg_id = target_data.get('message_id')
    origin_text = target_data.get('text', "")
    is_caption = target_data.get('is_caption', False)

    category_map = {
        CategoryButtons.CAT_0.value: 0,
        CategoryButtons.CAT_25.value: 25,
        CategoryButtons.CAT_50.value: 50,
        CategoryButtons.CAT_75.value: 75,
        CategoryButtons.CAT_100.value: 100,
    }
    
    selected_value = category_map.get(call.data)
    if selected_value is None:
         await call.answer("Ошибка данных категории", show_alert=True)
         return

    users = load_all_users()
    if target_user_id not in users:
        if str(target_user_id) in users:
            target_user_id = str(target_user_id)
        else:
            await call.answer("Пользователь не найден в базе", show_alert=True)
            return

    # 1. Обновляем данные пользователя
    users[target_user_id][UserFields.STATUS.value] = UserLifecycleStatus.CLIENT.value
    users[target_user_id][UserFields.CATEGORY.value] = selected_value
    
    current_balance = users[target_user_id].get(UserMetrics.BALANCE.value, 0)
    users[target_user_id][UserMetrics.BALANCE.value] = current_balance + selected_value
    
    save_all_users()

    # 2. Уведомляем пользователя
    try:
        msg = await bot.send_message(
            chat_id=int(target_user_id),
            text=(
                "🎉 **Поздравляем! Ваша анкета одобрена!**\n\n"
                "Теперь вы полноправный участник клуба.\n"
                f"Вам присвоена категория: **{selected_value}**\n"
                f"Ваш баланс пополнен на: **{selected_value}**\n\n"
                "Пользуйтесь меню для доступа к функциям."
            ),
            parse_mode="Markdown",
            reply_markup=get_persistent_main_menu()
        )
        add_message(global_msg_fast, int(target_user_id), msg)
    except Exception as e:
        await call.answer(f"Ошибка уведомления юзера: {e}", show_alert=True)

    # 3. Обновляем сообщение администратора (меню категорий)
    try:
        await call.message.delete()
    except Exception:
        pass
    
    try:
        await call.answer(f"Принято: Категория {selected_value} ✅")
    except Exception:
        pass

    # 4. Обновляем ИСХОДНОЕ сообщение заявки
    if origin_msg_id:
        new_text = f"{origin_text}\n\n✅ **ЗАЯВКА ПРИНЯТА**\nКатегория: {selected_value}"
        try:
             if is_caption:
                 await bot.edit_message_caption(
                     chat_id=call.message.chat.id,
                     message_id=origin_msg_id,
                     caption=new_text,
                     reply_markup=None
                 )
             else:
                 await bot.edit_message_text(
                     chat_id=call.message.chat.id,
                     message_id=origin_msg_id,
                     text=new_text,
                     reply_markup=None
                 )
        except Exception:
             pass

    # Чистим хранилище
    acceptance_targets.pop(admin_id, None)
