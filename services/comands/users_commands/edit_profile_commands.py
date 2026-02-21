import re
from handlers.fsm_utils import check_cancel_input, clear_waiting_input
from services.keyboards.edit_profile_keyboards import get_after_edit_keyboard, get_edit_profile_menu_keyboard
from services.msgs_utils.deleter_messages import clear_messages
from services.state_bot.global_store import add_message, global_msg_fast, global_msg_for_close
from services.users_utils.user_profile_manager import create_or_update_profile
from entity.Enums_entity import UserProfileFields, UserFlags, ChangesProfileStatus
from services.keyboards.creator_persistent_keyboards import get_persistent_main_menu
from services.users_utils.all_users_manager import update_user_field

async def send_error(message, user_id, text):
    msg = await message.answer(f"❌ {text}")
    add_message(global_msg_fast, user_id, msg)

async def send_after_edit_messages(message, user_id, confirmation_text):
    # 1. Первое сообщение: подтверждение изменения (с клавиатурой редактирования профиля)
    msg1 = await message.answer(
        text=confirmation_text,
        reply_markup=get_edit_profile_menu_keyboard(user_id)
    )
    add_message(global_msg_fast, user_id, msg1)

    # 2. Второе сообщение: вопрос о продолжении + основное меню
    msg2 = await message.answer(
        text="Хотите изменить что-то еще или сохранить?",
        reply_markup=get_edit_profile_menu_keyboard(user_id)
    )
    add_message(global_msg_for_close, user_id, msg2)

async def extract_and_update_name(message, state, user_id):
    text = (message.text or "").strip()
    
    if not text:
        await send_error(message, user_id, "Вы отправили не текст - введите его")
        return

    if await check_cancel_input(text, message, state):        
        # 2. Сообщение "Что нужно отредактировать" с inline клавиатурой (в fast)
        msg_menu = await message.answer(
            "что нужно отредактировать?",
            reply_markup=get_edit_profile_menu_keyboard(user_id)
        )
        add_message(global_msg_fast, user_id, msg_menu)
        return

    # Валидация ФИО
    if not (2 <= len(text) <= 100):
        await send_error(message, user_id, "Ошибка: имя должно быть от 2 до 100 символов")
        return
    
    if not re.match(r"^[a-zA-Zа-яА-ЯёЁ\s\-]+$", text):
        await send_error(message, user_id, "Ошибка: имя должно содержать только буквы, пробелы и дефис")
        return
        
    if len(text.split()) < 2:
        await send_error(message, user_id, "Ошибка: введите имя и фамилию (минимум 2 слова)")
        return

    await create_or_update_profile(user_id, {
        UserProfileFields.NAME.value: text
    })
    update_user_field(user_id, UserFlags.CHANGES_PROFILE_CONFIRMED.value, ChangesProfileStatus.PENDING_CHANGES.value)

    await clear_messages(user_id, global_msg_fast)
    await clear_waiting_input(state, message.chat.id, user_id)

    await send_after_edit_messages(message, user_id, f"✅ Имя успешно изменено на: {text}")


async def extract_and_update_area(message, state, user_id):
    text = (message.text or "").strip()
    if await check_cancel_input(text, message, state): 
        # 2. Сообщение "Что нужно отредактировать" с inline клавиатурой (в fast)
        msg_menu = await message.answer(
            "что нужно отредактировать?",
            reply_markup=get_edit_profile_menu_keyboard(user_id)
        )
        add_message(global_msg_fast, user_id, msg_menu)
        return
    
    # Валидация Района
    if not (2 <= len(text) <= 50):
         await send_error(message, user_id, "Ошибка: название района должно быть от 2 до 50 символов")
         return

    if not re.match(r"^[a-zA-Zа-яА-ЯёЁ\s\-]+$", text):
        await send_error(message, user_id, "Ошибка: район должен содержать только буквы, пробелы и дефис")
        return

    await create_or_update_profile(user_id, {
        UserProfileFields.AREA.value: text
    })
    update_user_field(user_id, UserFlags.CHANGES_PROFILE_CONFIRMED.value, ChangesProfileStatus.PENDING_CHANGES.value)

    await clear_messages(user_id, global_msg_fast)
    await clear_waiting_input(state, message.chat.id, user_id)

    await send_after_edit_messages(message, user_id, f"✅ Район успешно изменен на: {text}")


async def extract_and_update_product_name(message, state, user_id):
    text = (message.text or "").strip()
    if await check_cancel_input(text, message, state):
        # 2. Сообщение "Что нужно отредактировать" с inline клавиатурой (в fast)
        msg_menu = await message.answer(
            "что нужно отредактировать?",
            reply_markup=get_edit_profile_menu_keyboard(user_id)
        )
        add_message(global_msg_fast, user_id, msg_menu)
        return

    # Валидация Услуги
    if not (3 <= len(text) <= 30):
        await send_error(message, user_id, "Ошибка: название услуги должно быть от 3 до 30 символов")
        return

    if not re.match(r"^[a-zA-Zа-яА-ЯёЁ\s\-\./]+$", text):
        await send_error(message, user_id, "Ошибка: недопустимые символы в названии услуги")
        return

    await create_or_update_profile(user_id, {
        UserProfileFields.SERVICE_NAME.value: text
    })
    update_user_field(user_id, UserFlags.CHANGES_PROFILE_CONFIRMED.value, ChangesProfileStatus.PENDING_CHANGES.value)

    await clear_messages(user_id, global_msg_fast)
    await clear_waiting_input(state, message.chat.id, user_id)

    await send_after_edit_messages(message, user_id, f"✅ Название услуги изменено на: {text}")


async def extract_and_update_description(message, state, user_id):
    text = (message.text or "").strip()
    if await check_cancel_input(text, message, state):        
        # 2. Сообщение "Что нужно отредактировать" с inline клавиатурой (в fast)
        msg_menu = await message.answer(
            "что нужно отредактировать?",
            reply_markup=get_edit_profile_menu_keyboard(user_id)
        )
        add_message(global_msg_fast, user_id, msg_menu)
        return
    
    # Валидация Описания
    if not (100 <= len(text) <= 500):
        await send_error(message, user_id, f"Ошибка: описание должно быть от 100 до 500 символов (сейчас {len(text)})")
        return

    if re.search(r"[\U00010000-\U0010ffff]", text):
         await send_error(message, user_id, "Ошибка: использование эмодзи в описании запрещено")
         return

    await create_or_update_profile(user_id, {
        UserProfileFields.SERVICE_DESCRIPTION.value: text
    })
    update_user_field(user_id, UserFlags.CHANGES_PROFILE_CONFIRMED.value, ChangesProfileStatus.PENDING_CHANGES.value)

    await clear_messages(user_id, global_msg_fast)
    await clear_waiting_input(state, message.chat.id, user_id)

    await send_after_edit_messages(message, user_id, "✅ Описание услуги обновлено.")


async def extract_and_update_price(message, state, user_id):
    text = (message.text or "").strip()
    if await check_cancel_input(text, message, state):
               
        # 2. Сообщение "Что нужно отредактировать" с inline клавиатурой (в fast)
        msg_menu = await message.answer(
            "что нужно отредактировать?",
            reply_markup=get_edit_profile_menu_keyboard(user_id)
        )
        add_message(global_msg_fast, user_id, msg_menu)
        return

    # Валидация Прайса
    if not text.isdigit():
        await send_error(message, user_id, "Ошибка: цена должна быть целым числом")
        return
        
    price_val = int(text)
    if not (1 <= price_val <= 99):
        await send_error(message, user_id, "Ошибка: цена должна быть от 1 до 99")
        return

    await create_or_update_profile(user_id, {
        UserProfileFields.PRICE_INFO.value: text
    })
    update_user_field(user_id, UserFlags.CHANGES_PROFILE_CONFIRMED.value, ChangesProfileStatus.PENDING_CHANGES.value)

    await clear_messages(user_id, global_msg_fast)
    await clear_waiting_input(state, message.chat.id, user_id)

    await send_after_edit_messages(message, user_id, f"✅ Прайс изменен на: {text}")
