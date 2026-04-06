"""
Команды пошагового ввода при редактировании/добавлении услуг через временный файл.
Валидация аналогична to_set_profile_commands.py при регистрации.
"""

from services.keyboards.creator_persistent_keyboards import get_persistent_main_menu
import re
from handlers.fsm_utils import clear_waiting_input, set_waiting_input, check_cancel_input
from services.msgs_utils.deleter_messages import clear_messages
from services.state_bot.global_store import add_message, global_msg_fast
from services.users_utils.temp_profile_manager import get_temp_profile, update_temp_profile
from entity.Enums_entity import UserProfileFields
from services.keyboards.bot_all_buttons import ProcessChangingProfileButtons
from services.keyboards.edit_profile_keyboards import get_keyboard_for_changing_profile
import html


async def _send_error(message, user_id, text):
    msg = await message.answer(f"❌ {text}")
    add_message(global_msg_fast, user_id, msg)


# ========================================================
# ПРОСТЫЕ ПОЛЯ (имя, район, деятельность, описание, ссылки)
# ========================================================

async def handle_edit_temp_name(message, state, user_id, bot):
    """Редактирование имени через временный профиль."""
    if await check_cancel_input(message.text, message, state):
        await clear_messages(user_id, global_msg_fast)
        await clear_waiting_input(state, message.chat.id, message.from_user.id)
        msg = await bot.send_message(chat_id = user_id, text = "Вы в режиме редактирования профиля",
            reply_markup=get_keyboard_for_changing_profile()
        )
        add_message(global_msg_fast, user_id, msg)
        return


    text = (message.text or "").strip()
    if not text:
        await _send_error(message, user_id, "Нужен текст — картинки и файлы здесь не подойдут 🙏")
        return


    if not (2 <= len(text) <= 100):
        await _send_error(message, user_id, "Ошибка: имя должно быть от 2 до 100 символов")
        return

    if not re.match(r"^[a-zA-Zа-яА-ЯёЁ\s\-]+$", text):
        await _send_error(message, user_id, "Ошибка: имя должно содержать только буквы, пробелы и дефис")
        return

    if len(text.split()) < 2:
        await _send_error(message, user_id, "Ошибка: введите имя и фамилию (минимум 2 слова)")
        return

    update_temp_profile(user_id, {UserProfileFields.NAME.value: text})

    await clear_messages(user_id, global_msg_fast)
    await clear_waiting_input(state, message.chat.id, user_id)

    await message.answer(
        f"...: {text}",
        reply_markup=get_persistent_main_menu()
    )
    msg = await message.answer(
        f"✅ Имя изменено на: {text}",
        reply_markup=get_keyboard_for_changing_profile()
    )
    add_message(global_msg_fast, user_id, msg)


async def handle_edit_temp_area(message, state, user_id, bot):
    """Редактирование района через временный профиль."""
    if await check_cancel_input(message.text, message, state):
        await clear_messages(user_id, global_msg_fast)
        await clear_waiting_input(state, message.chat.id, message.from_user.id)
        msg = await bot.send_message(chat_id = user_id, text = "Вы в режиме редактирования профиля",
            reply_markup=get_keyboard_for_changing_profile()
        )
        add_message(global_msg_fast, user_id, msg)
        return



    text = (message.text or "").strip()
    if not text:
        await _send_error(message, user_id, "Нужен текст")
        return

    if not (2 <= len(text) <= 50):
        await _send_error(message, user_id, "Ошибка: название района должно быть от 2 до 50 символов")
        return

    if not re.match(r"^[a-zA-Zа-яА-ЯёЁ\s\-,]+$", text):
        await _send_error(message, user_id, "Ошибка: район должен содержать только буквы, пробелы, дефис или запятую")
        return

    update_temp_profile(user_id, {UserProfileFields.AREA.value: text})

    await clear_messages(user_id, global_msg_fast)
    await clear_waiting_input(state, message.chat.id, user_id)

    await message.answer(
        f"...: {text}",
        reply_markup=get_persistent_main_menu()
    )
    msg = await message.answer(
        f"✅ Район изменён на: {text}",
        reply_markup=get_keyboard_for_changing_profile()
    )
    add_message(global_msg_fast, user_id, msg)


async def handle_edit_temp_profession(message, state, user_id, bot):
    """Редактирование деятельности через временный профиль."""

    if await check_cancel_input(message.text, message, state):
        await clear_messages(user_id, global_msg_fast)
        await clear_waiting_input(state, message.chat.id, message.from_user.id)
        msg = await bot.send_message(chat_id = user_id, text = "Вы в режиме редактирования профиля",
            reply_markup=get_keyboard_for_changing_profile()
        )
        add_message(global_msg_fast, user_id, msg)
        return
    text = (message.text or "").strip()
    if not text:
        await _send_error(message, user_id, "Нужен текст")
        return

    if not (2 <= len(text) <= 50):
        await _send_error(message, user_id, "Ошибка: название деятельности должно быть от 2 до 50 символов")
        return

    update_temp_profile(user_id, {UserProfileFields.PROFESSION.value: text})

    await clear_messages(user_id, global_msg_fast)
    await clear_waiting_input(state, message.chat.id, user_id)

    await message.answer(
        f"...: {text}",
        reply_markup=get_persistent_main_menu()
    )
    msg = await message.answer(
        f"✅ Деятельность изменена на: {text}",
        reply_markup=get_keyboard_for_changing_profile()
    )
    add_message(global_msg_fast, user_id, msg)


async def handle_edit_temp_description(message, state, user_id, bot):
    """Редактирование описания (о себе) через временный профиль."""
    if await check_cancel_input(message.text, message, state):
        await clear_messages(user_id, global_msg_fast)
        await clear_waiting_input(state, message.chat.id, message.from_user.id)
        msg = await bot.send_message(chat_id = user_id, text = "Вы в режиме редактирования профиля",
            reply_markup=get_keyboard_for_changing_profile()
        )
        add_message(global_msg_fast, user_id, msg)
        return

    text = (message.text or "").strip()
    if not text:
        await _send_error(message, user_id, "Нужен текст")
        return

    if not (50 <= len(text) <= 300):
        await _send_error(message, user_id, f"Ошибка: описание должно быть от 50 до 300 символов (сейчас {len(text)})")
        return

    update_temp_profile(user_id, {UserProfileFields.DESCRIPTION_PROFESSION.value: text})

    await clear_messages(user_id, global_msg_fast)
    await clear_waiting_input(state, message.chat.id, user_id)

    await message.answer(
        f"...: {text}",
        reply_markup=get_persistent_main_menu()
    )
    msg = await message.answer(
        "✅ Описание о себе обновлено.",
        reply_markup=get_keyboard_for_changing_profile()
    )
    add_message(global_msg_fast, user_id, msg)


async def handle_edit_temp_socials(message, state, user_id, bot):
    """Редактирование ссылок через временный профиль."""
    if await check_cancel_input(message.text, message, state):
        await clear_messages(user_id, global_msg_fast)
        await clear_waiting_input(state, message.chat.id, message.from_user.id)
        msg = await bot.send_message(chat_id = user_id, text = "Вы в режиме редактирования профиля",
            reply_markup=get_keyboard_for_changing_profile()
        )
        add_message(global_msg_fast, user_id, msg)
        return

    text = (message.text or "").strip()
    if not text:
        await _send_error(message, user_id, "Нужен текст")
        return

    clean_text = text.replace(',', ' ').replace('\n', ' ')
    links = [link.strip() for link in clean_text.split() if link.strip()]

    if not (1 <= len(links) <= 10):
        await _send_error(message, user_id, f"Ошибка: укажите от 1 до 10 ссылок (вы указали {len(links)})")
        return

    update_temp_profile(user_id, {UserProfileFields.SOCIAL_LINKS.value: links})

    await clear_messages(user_id, global_msg_fast)
    await clear_waiting_input(state, message.chat.id, user_id)

    await message.answer(
        f"...: {text}",
        reply_markup=get_persistent_main_menu()
    )
    msg = await message.answer(
        "✅ Ссылки обновлены.",
        reply_markup=get_keyboard_for_changing_profile()
    )
    add_message(global_msg_fast, user_id, msg)
