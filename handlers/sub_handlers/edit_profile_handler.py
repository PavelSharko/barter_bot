from aiogram import Bot
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from services.keyboards.bot_all_buttons import EditProfileButtons, MainMenuButtons
from services.keyboards.sustem_inline_keyboard import get_inline_keyboard_close
from services.state_bot.global_store import add_message, global_msg_fast
from services.keyboards.edit_profile_keyboards import get_edit_profile_menu_keyboard
from services.msgs_utils.deleter_messages import clear_messages
from handlers.fsm_utils import set_waiting_input
from initApp.config_loader import config
from services.keyboards.creator_persistent_keyboards import get_cancel_keyboard

async def handle_edit_profile_callbacks(bot: Bot, call: CallbackQuery, state: FSMContext):
    """
    Обработчик кнопок редактирования профиля.
    """
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    data = call.data
    await clear_messages(call.from_user.id, global_msg_fast)

    

    # # 1. Меню редактирования (список кнопок)
    if data == EditProfileButtons.EDIT_PROFILE_MENU.name.lower():
        await call.answer()
        msg = await call.message.answer(
            f"Для редактирвания профиля напишите модератору {config.MODERATOR_USERNAME}",
            reply_markup=get_inline_keyboard_close()
        )
        add_message(global_msg_fast, user_id, msg)
        return
         # todo: заменить реализацию выше на закоментированную - так как это не платил заказчик но уже это готово наполивну
        # await clear_messages(user_id, global_msg_fast)
        # msg = await call.message.answer(
        #     "📝 Выберите, что вы хотите изменить:",
        #     reply_markup=get_edit_profile_menu_keyboard(user_id)
        # )
        # add_message(global_msg_fast, user_id, msg)
        # await call.answer()
        # return

    # 2. Сохранить изменения (выход из режима редактирования)
    elif data == EditProfileButtons.SAVE_CHANGES.name.lower():
        from services.users_utils.all_users_manager import update_user_field
        from entity.Enums_entity import UserFlags, ChangesProfileStatus, UserProfileFields
        from services.keyboards.edit_profile_keyboards import get_moderator_approval_changes_keyboard
        from services.users_utils.user_profile_manager import get_profile
        from services.keyboards.creator_persistent_keyboards import get_persistent_main_menu
        # Меняем статус
        update_user_field(user_id, UserFlags.CHANGES_PROFILE_CONFIRMED.value, ChangesProfileStatus.WAITING_CONFIRMATION.value)
        
        # Формируем красивый текст анкеты
        profile = get_profile(user_id) or {}
        name = profile.get(UserProfileFields.NAME.value) or "Не указано"
        area = profile.get(UserProfileFields.AREA.value) or "Не указано"
        desc_prof = profile.get(UserProfileFields.DESCRIPTION_PROFESSION.value) or "Не указано"
        links = "\n".join(profile.get(UserProfileFields.SOCIAL_LINKS.value, [])) or "Не указано"

        import html
        moderator_text = (
            f"⚠️ <b>Клиент внес изменения в профиль!</b>\n"
            f"ID: <code>{user_id}</code>\n"
            f"Username: @{html.escape(str(call.from_user.username))}\n\n"
            f"<b>ФИО</b>: {html.escape(str(name))}\n"
            f"<b>Район</b>: {html.escape(str(area))}\n"
            f"<b>О себе</b>: {html.escape(str(desc_prof))}\n"
            f"<b>Ссылки</b>: \n{html.escape(str(links))}\n\n"
        )
        services = profile.get(UserProfileFields.SERVICES.value, [])
        if services:
            moderator_text += "<b>Услуги:</b>\n"
            for i, s in enumerate(services, 1):
                moderator_text += f"{i}. <b>{html.escape(str(s.get('name', '')))}</b>\n"
                moderator_text += f"   <i>Описание</i>: {html.escape(str(s.get('description', '')))}\n"
                moderator_text += f"   <i>Прайс</i>: {html.escape(str(s.get('price', '')))}\n\n"
        else:
            moderator_text += "<b>Услуги отсутствуют.</b>\n"
        try:
            msg_mod = await bot.send_message(
                chat_id=config.MODERATOR_CONTACT_ID,
                text=moderator_text,
                parse_mode="HTML",
                reply_markup=get_moderator_approval_changes_keyboard(user_id)
            )
        except Exception as e:
            print(f"Ошибка отправки модератору: {e}")
            
        await bot.send_message(chat_id=user_id, text="Изменения отправлены на модерацию ✅")
        await call.answer()
        await clear_messages(user_id, global_msg_fast)
        
        msg = await call.message.answer(
            "Ваши изменения успешно отправлены на проверку модератору.",
            reply_markup=get_persistent_main_menu()
        )
        add_message(global_msg_fast, user_id, msg)
        return

    # 3. Обработка конкретных кнопок редактирования
    # Паттерн: Очистить -> Set State -> Ask User -> Add to clear list
    
    command_name = None
    prompt_text = ""

    if data == EditProfileButtons.EDIT_NAME.name.lower():
        command_name = EditProfileButtons.EDIT_NAME.value.lower()
        prompt_text = "Введите новое имя (ФИО, минимум 2 слова):"
        
    elif data == EditProfileButtons.EDIT_AREA.name.lower():
        command_name = EditProfileButtons.EDIT_AREA.value.lower()
        prompt_text = "Введите новый район:"

    elif data == EditProfileButtons.EDIT_NAME_PRODUCT.name.lower():
        command_name = EditProfileButtons.EDIT_NAME_PRODUCT.value.lower()
        prompt_text = "Введите новое название услуги/товара:"

    elif data == EditProfileButtons.EDIT_FULL_INFO_PRODUCT.name.lower():
        command_name = EditProfileButtons.EDIT_FULL_INFO_PRODUCT.value.lower()
        prompt_text = "Введите новое описание (100-500 символов):"

    elif data == EditProfileButtons.EDIT_PRICE.name.lower():
        command_name = EditProfileButtons.EDIT_PRICE.value.lower()
        prompt_text = "Введите новый прайс (число 1-99):"

    if command_name:
        await clear_messages(user_id, global_msg_fast)
        await set_waiting_input(state, bot, chat_id, user_id, command_name, timeout=config.TIME_TO_INPUT_MSG_FSM)
        
        msg = await call.message.answer(
            f"✏️ {prompt_text}",
            reply_markup=get_cancel_keyboard()
        )
        add_message(global_msg_fast, user_id, msg)
        await call.answer()
        return

    # Если кнопка не распознана
    await bot.send_message(chat_id=user_id, text="Неизвестная кнопка")
    await call.answer()
