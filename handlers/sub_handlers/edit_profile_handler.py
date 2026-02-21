from aiogram import Bot
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from services.keyboards.bot_all_buttons import EditProfileButtons, MainMenuButtons
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
        service = profile.get(UserProfileFields.SERVICE_NAME.value) or "Не указано"
        desc = profile.get(UserProfileFields.SERVICE_DESCRIPTION.value) or "Не указано"
        price = profile.get(UserProfileFields.PRICE_INFO.value) or "Не указано"
        links = "\n".join(profile.get(UserProfileFields.SOCIAL_LINKS.value, [])) or "Не указано"
        
        moderator_text = (
            f"⚠️ **Клиент внес изменения в профиль!**\n"
            f"ID: `{user_id}`\n"
            f"Username: @{call.from_user.username}\n\n"
            f"**ФИО**: {name}\n"
            f"**Район**: {area}\n"
            f"**Товар/Услуга**: {service}\n"
            f"**Описание**: {desc}\n"
            f"**Прайс**: {price}\n"
            f"**Ссылки**: \n{links}\n"
        )
        
        try:
            msg_mod = await bot.send_message(
                chat_id=config.MODERATOR_CONTACT_ID,
                text=moderator_text,
                parse_mode="Markdown",
                reply_markup=get_moderator_approval_changes_keyboard(user_id)
            )
        except Exception as e:
            print(f"Ошибка отправки модератору: {e}")
            
        await call.answer("Изменения отправлены на модерацию ✅")
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
    await call.answer("Неизвестная кнопка", show_alert=True)
