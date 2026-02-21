from aiogram import Bot
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from services.keyboards.bot_all_buttons import MainMenuButtons
from services.msgs_utils.deleter_messages import clear_messages
from services.state_bot.global_store import add_message, global_msg_fast
from handlers.fsm_utils import set_waiting_input
from initApp.config_loader import config
from services.users_utils.user_profile_manager import load_profiles
from entity.Enums_entity import UserProfileFields, UserMetrics
from services.keyboards.creator_inline_keyboards import get_profile_view_keyboard
from services.comands.users_commands.show_balance import show_user_balance
from services.users_utils.all_users_manager import load_all_users
from services.keyboards.sustem_inline_keyboard import get_inline_keyboard_close


async def handle_callback_main_menu_for_users(call: CallbackQuery, bot: Bot, state: FSMContext):
    """
    Обработчик callback-кнопок главного меню пользователя.
    """
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    data = call.data

    # 1. Посмотреть свой профиль
    if data == MainMenuButtons.VIEW_PROFILE.name.lower():
        await clear_messages(user_id, global_msg_fast)
        
        await call.answer()
        
        profiles = load_profiles()
        user_profile = profiles.get(user_id) or profiles.get(str(user_id))
        
        if not user_profile:
             msg = await call.message.answer("⚠️ Профиль не найден.")
             add_message(global_msg_fast, user_id, msg)
             return

        text = (
            f"👤 **Ваш профиль:**\n\n"
            f"**Имя:** {user_profile.get(UserProfileFields.NAME.value, 'Не указано')}\n"
            f"**Район:** {user_profile.get(UserProfileFields.AREA.value, 'Не указано')}\n"
            f"**Услуга/Товар:** {user_profile.get(UserProfileFields.SERVICE_NAME.value, 'Не указано')}\n"
            f"**Описание:** {user_profile.get(UserProfileFields.SERVICE_DESCRIPTION.value, 'Не указано')}\n"
            f"**Прайс:** {user_profile.get(UserProfileFields.PRICE_INFO.value, 'Не указано')}\n"
        )
        
        msg = await call.message.answer(
            text,
            reply_markup=get_profile_view_keyboard(),
            parse_mode="Markdown"
        )
        add_message(global_msg_fast, user_id, msg)
        return

    # 2. Мой баланс
    elif data == MainMenuButtons.VIEW_MY_BALANCE.name.lower():
        await show_user_balance(call, bot) 
        return

    # 3. Баланс других
    elif data == MainMenuButtons.VIEW_OTHERS_BALANCE.name.lower():
        await call.answer()
        
        users = load_all_users()
        profiles = load_profiles()
        
        total_balance = 0
        user_balances = []
        
        for u_id, u_data in users.items():
            balance = u_data.get(UserMetrics.BALANCE.value, 0)
            total_balance += balance
            
            if balance == 0:
                continue
                
            # Попытка получить имя из профиля, если его нет - берём из users
            u_profile = profiles.get(u_id) or profiles.get(str(u_id)) or {}
            name = u_profile.get(UserProfileFields.NAME.value)
            if not name:
                from entity.Enums_entity import UserFields
                name = u_data.get(UserFields.NAME_REAL.value) or u_data.get(UserFields.NAME_TG.value) or f"ID{u_id}"
                
            user_balances.append((name, balance))
            
        user_balances.sort(key=lambda x: x[1], reverse=True)
        
        text = f"** ОБЩИЙ БАЛАНС МОНЕТ В КЛУБЕ 🪙 - {total_balance}**\n\n"
        for name, balance in user_balances:
            text += f"- {name} - {balance} монет\n"
            
        msg = await call.message.answer(
            text, 
            parse_mode="Markdown",
            reply_markup=get_inline_keyboard_close()
        )
        add_message(global_msg_fast, user_id, msg)
        return

    # 4. История сделок
    elif data == MainMenuButtons.VIEW_DEALS_HISTORY.name.lower():
        await call.answer()
        msg = await call.message.answer(f"Поймали колбек: {MainMenuButtons.VIEW_DEALS_HISTORY.value}")
        add_message(global_msg_fast, user_id, msg)
        return

    # 5. Найти услугу/товар & Возврат назад
    elif data in (MainMenuButtons.FIND_SERVICE.name.lower(), MainMenuButtons.BACK_TO_SERVICES.name.lower()):
        await call.answer()
        from services.keyboards.creator_inline_keyboards import get_find_service_keyboard
        
        msg = await call.message.answer(
            "Вот список доступных услуг на острове Бали:", 
            reply_markup=get_find_service_keyboard()
        )
        add_message(global_msg_fast, user_id, msg)
        return

    # 5.1 Нажатие на конкретную услугу из списка "Найти услугу/товар" (ищем профиль)
    elif data.startswith(f"{MainMenuButtons.FIND_SERVICE.name.lower()}_"):
        await call.answer()
        # Парсим ID из строки `find_service_ID`
        try:
            _, target_id_str = data.rsplit('_', 1)
            target_id = int(target_id_str)
        except Exception:
            return
            
        profiles = load_profiles()
        target_profile = profiles.get(target_id) or profiles.get(str(target_id))
        
        if not target_profile:
             msg = await call.message.answer("⚠️ Профиль этого пользователя не найден.")
             add_message(global_msg_fast, user_id, msg)
             return
             
        from services.keyboards.creator_inline_keyboards import get_service_profile_keyboard     

        text = (
            f"👤 **Профиль услуги:**\n\n"
            f"**Имя:** {target_profile.get(UserProfileFields.NAME.value, 'Не указано')}\n"
            f"**Район:** {target_profile.get(UserProfileFields.AREA.value, 'Не указано')}\n"
            f"**Услуга/Товар:** {target_profile.get(UserProfileFields.SERVICE_NAME.value, 'Не указано')}\n"
            f"**Описание:** {target_profile.get(UserProfileFields.SERVICE_DESCRIPTION.value, 'Не указано')}\n"
            f"**Прайс:** {target_profile.get(UserProfileFields.PRICE_INFO.value, 'Не указано')}\n"
        )
            
        msg = await call.message.answer(
            text,
            reply_markup=get_service_profile_keyboard(target_id_str),
            parse_mode="Markdown"
        )
        add_message(global_msg_fast, user_id, msg)
        return

    # 5.2 Заглушка: просмотр отзывов чужого профиля
    elif data.startswith(f"{MainMenuButtons.REVIEWS.name.lower()}_"):
        await call.answer()
        try:
            _, target_id_str = data.rsplit('_', 1)
        except Exception:
            return
        msg = await call.message.answer(
            f"Поймали запрос на просмотр отзыва юзера с айди {target_id_str}",
            reply_markup=get_inline_keyboard_close()
        )
        add_message(global_msg_fast, user_id, msg)
        return

    # 5.3 Заглушка: создание сделки с чужим профилем
    elif data.startswith(f"{MainMenuButtons.CREATE_DEAL.name.lower()}_"):
        await call.answer()
        try:
            _, target_id_str = data.rsplit('_', 1)
        except Exception:
            return
        msg = await call.message.answer(
            f"Поймали запрос на создание сделки с юзером с айди {target_id_str}",
            reply_markup=get_inline_keyboard_close()
        )
        add_message(global_msg_fast, user_id, msg)
        return

    # 6. Подтвердить сделку
    elif data == MainMenuButtons.CONFIRM_DEAL.name.lower():
        await call.answer()
        msg = await call.message.answer(f"Поймали колбек: {MainMenuButtons.CONFIRM_DEAL.value}")
        add_message(global_msg_fast, user_id, msg)
        return

    # 7. Поддержка
    elif data == MainMenuButtons.SUPPORT.name.lower():
        await call.answer()
        msg = await call.message.answer(
            f"Для решения любых вопросов вы можете написать нашему модератору {config.MODERATOR_USERNAME}",
            reply_markup=get_inline_keyboard_close()
        )
        add_message(global_msg_fast, user_id, msg)
        return
