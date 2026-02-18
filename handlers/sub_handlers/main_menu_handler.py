from aiogram import Bot
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from services.keyboards.bot_all_buttons import MainMenuButtons
from services.state_bot.global_store import add_message, global_msg_fast
from handlers.fsm_utils import set_waiting_input
from initApp.config_loader import config
from services.users_utils.user_profile_manager import load_profiles
from entity.Enums_entity import UserProfileFields
from services.keyboards.creator_inline_keyboards import get_profile_view_keyboard
from services.comands.users_commands.show_balance import show_user_balance

async def handle_callback_main_menu_for_users(call: CallbackQuery, bot: Bot, state: FSMContext):
    """
    Обработчик callback-кнопок главного меню пользователя.
    """
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    data = call.data

    # 1. Посмотреть свой профиль
    if data == MainMenuButtons.VIEW_PROFILE.name.lower():
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
        msg = await call.message.answer(f"Поймали колбек: {MainMenuButtons.VIEW_OTHERS_BALANCE.value}")
        add_message(global_msg_fast, user_id, msg)
        return

    # 4. История сделок
    elif data == MainMenuButtons.VIEW_DEALS_HISTORY.name.lower():
        await call.answer()
        msg = await call.message.answer(f"Поймали колбек: {MainMenuButtons.VIEW_DEALS_HISTORY.value}")
        add_message(global_msg_fast, user_id, msg)
        return

    # 5. Найти услугу/товар
    elif data == MainMenuButtons.FIND_SERVICE.name.lower():
        await call.answer()
        msg = await call.message.answer(f"Поймали колбек: {MainMenuButtons.FIND_SERVICE.value}")
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
        msg = await call.message.answer(f"Поймали колбек: {MainMenuButtons.SUPPORT.value}")
        add_message(global_msg_fast, user_id, msg)
        return
