"""
Команды пошагового ввода при редактировании/добавлении услуг через временный файл.
Валидация аналогична to_set_profile_commands.py при регистрации.
"""

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
# РЕДАКТИРОВАНИЕ СУЩЕСТВУЮЩЕЙ УСЛУГИ (3 шага: имя → описание → цена)
# ========================================================

async def handle_edit_service_name_input(message, state, user_id):
    """Шаг 1: Ввод нового названия услуги."""
    text = (message.text or "").strip()
    if not text:
        await _send_error(message, user_id, "Нужен текст — картинки и файлы здесь не подойдут 🙏")
        return

    if not (2 <= len(text) <= 50):
        await _send_error(message, user_id, "Ошибка: название услуги должно быть от 2 до 50 символов")
        return

    # Получаем индекс из FSM
    fsm_data = await state.get_data()
    service_idx = fsm_data.get("editing_service_idx", 0)

    # Сохраняем новое имя во временный профиль
    temp = get_temp_profile(user_id) or {}
    services = temp.get(UserProfileFields.SERVICES.value, [])
    if service_idx < len(services):
        old_desc = html.escape(str(services[service_idx].get('description', 'Нет описания')))
        services[service_idx]['name'] = text
        update_temp_profile(user_id, {UserProfileFields.SERVICES.value: services})

    await clear_messages(user_id, global_msg_fast)
    await clear_waiting_input(state, message.chat.id, user_id)

    prompt = (
        f"✅ Супер — название изменили!\n\n"
        f"Теперь введите описание услуги.\n"
        f"Ранее услуга описывалась так:\n<i>{old_desc}</i>\n\n"
        f"Введите новое описание (от 50 до 300 символов):"
    )
    msg = await message.answer(prompt, parse_mode="HTML")
    add_message(global_msg_fast, user_id, msg)
    await set_waiting_input(state, None, message.chat.id, user_id, ProcessChangingProfileButtons.EDIT_SERVICE_DESC_INPUT.value)
    await state.update_data(editing_service_idx=service_idx)


async def handle_edit_service_desc_input(message, state, user_id):
    """Шаг 2: Ввод нового описания услуги."""
    text = (message.text or "").strip()
    if not text:
        await _send_error(message, user_id, "Нужен текст — картинки и файлы здесь не подойдут 🙏")
        return

    if not (50 <= len(text) <= 300):
        await _send_error(message, user_id, f"Ошибка: описание должно быть от 50 до 300 символов (сейчас {len(text)})")
        return

    fsm_data = await state.get_data()
    service_idx = fsm_data.get("editing_service_idx", 0)

    temp = get_temp_profile(user_id) or {}
    services = temp.get(UserProfileFields.SERVICES.value, [])
    if service_idx < len(services):
        services[service_idx]['description'] = text
        update_temp_profile(user_id, {UserProfileFields.SERVICES.value: services})

    await clear_messages(user_id, global_msg_fast)
    await clear_waiting_input(state, message.chat.id, user_id)

    prompt = (
        f"✅ Описание сохранено!\n\n"
        f"Теперь введите цену услуги в долларах (целое число от 1 до 200).\n"
        f"1$ = 1 монета клуба 🪙"
    )
    msg = await message.answer(prompt)
    add_message(global_msg_fast, user_id, msg)
    await set_waiting_input(state, None, message.chat.id, user_id, ProcessChangingProfileButtons.EDIT_SERVICE_PRICE_INPUT.value)
    await state.update_data(editing_service_idx=service_idx)


async def handle_edit_service_price_input(message, state, user_id):
    """Шаг 3: Ввод новой цены услуги."""
    text = (message.text or "").strip()

    if not text.isdigit():
        await _send_error(message, user_id, "Ошибка: цена должна быть целым числом")
        return

    price_val = int(text)
    if not (1 <= price_val <= 200):
        await _send_error(message, user_id, "Ошибка: цена услуги должна быть от 1 до 200 монет")
        return

    fsm_data = await state.get_data()
    service_idx = fsm_data.get("editing_service_idx", 0)

    temp = get_temp_profile(user_id) or {}
    services = temp.get(UserProfileFields.SERVICES.value, [])
    if service_idx < len(services):
        services[service_idx]['price'] = text
        update_temp_profile(user_id, {UserProfileFields.SERVICES.value: services})

    await clear_messages(user_id, global_msg_fast)
    await clear_waiting_input(state, message.chat.id, user_id)

    msg = await message.answer(
        "Отлично, услуга была изменена ✅",
        reply_markup=get_keyboard_for_changing_profile()
    )
    add_message(global_msg_fast, user_id, msg)


# ========================================================
# ДОБАВЛЕНИЕ НОВОЙ УСЛУГИ (3 шага: имя → описание → цена)
# ========================================================

async def handle_add_service_name_input(message, state, user_id):
    """Шаг 1: Ввод названия новой услуги."""
    text = (message.text or "").strip()
    if not text:
        await _send_error(message, user_id, "Нужен текст — картинки и файлы здесь не подойдут 🙏")
        return

    if not (2 <= len(text) <= 50):
        await _send_error(message, user_id, "Ошибка: название услуги должно быть от 2 до 50 символов")
        return

    # Сохраняем имя во временную переменную FSM
    await clear_messages(user_id, global_msg_fast)
    await clear_waiting_input(state, message.chat.id, user_id)

    prompt = (
        f"✅ Отлично! Услуга: {html.escape(text)}\n\n"
        "Теперь подробно, но кратко опишите детали услуги (что входит, нюансы).\n"
        "Также укажите условия отмены — за какое время вы готовы принять отмену без последствий.\n\n"
        "⚠️ Пожалуйста, не пишите в этом разделе цену — для неё будет отдельный шаг.\n\n"
        "Описание должно быть от 50 до 300 символов."
    )
    msg = await message.answer(prompt)
    add_message(global_msg_fast, user_id, msg)
    await set_waiting_input(state, None, message.chat.id, user_id, ProcessChangingProfileButtons.ADD_SERVICE_DESC_INPUT.value)
    await state.update_data(new_service_name=text)


async def handle_add_service_desc_input(message, state, user_id):
    """Шаг 2: Ввод описания новой услуги."""
    text = (message.text or "").strip()
    if not text:
        await _send_error(message, user_id, "Нужен текст — картинки и файлы здесь не подойдут 🙏")
        return

    if not (50 <= len(text) <= 300):
        await _send_error(message, user_id, f"Ошибка: описание должно быть от 50 до 300 символов (сейчас {len(text)})")
        return

    fsm_data = await state.get_data()
    service_name = fsm_data.get("new_service_name", "Услуга")

    await clear_messages(user_id, global_msg_fast)
    await clear_waiting_input(state, message.chat.id, user_id)

    prompt = (
        f"✅ Описание добавлено!\n\n"
        f"Укажите прайс в долларах целым числом (от 1 до 200) — 1$ = 1 монета клуба 🪙\n\n"
        f"Цену здесь лучше поставить такую же, как вне клуба, или чуть ниже — но не выше 😊"
    )
    msg = await message.answer(prompt)
    add_message(global_msg_fast, user_id, msg)
    await set_waiting_input(state, None, message.chat.id, user_id, ProcessChangingProfileButtons.ADD_SERVICE_PRICE_INPUT.value)
    await state.update_data(new_service_name=service_name, new_service_desc=text)


async def handle_add_service_price_input(message, state, user_id):
    """Шаг 3: Ввод цены новой услуги."""
    text = (message.text or "").strip()

    if not text.isdigit():
        await _send_error(message, user_id, "Ошибка: цена должна быть целым числом")
        return

    price_val = int(text)
    if not (1 <= price_val <= 200):
        await _send_error(message, user_id, "Ошибка: цена услуги должна быть от 1 до 200 монет")
        return

    fsm_data = await state.get_data()
    service_name = fsm_data.get("new_service_name", "Услуга")
    service_desc = fsm_data.get("new_service_desc", "")

    # Добавляем услугу во временный профиль
    temp = get_temp_profile(user_id) or {}
    services = temp.get(UserProfileFields.SERVICES.value, [])
    services.append({
        'name': service_name,
        'description': service_desc,
        'price': text
    })
    update_temp_profile(user_id, {UserProfileFields.SERVICES.value: services})

    await clear_messages(user_id, global_msg_fast)
    await clear_waiting_input(state, message.chat.id, user_id)

    msg = await message.answer(
        "✅ Услуга добавлена!",
        reply_markup=get_keyboard_for_changing_profile()
    )
    add_message(global_msg_fast, user_id, msg)


# ========================================================
# ПРОСТЫЕ ПОЛЯ (имя, район, деятельность, описание, ссылки)
# ========================================================

async def handle_edit_temp_name(message, state, user_id, bot):
    """Редактирование имени через временный профиль."""
    if await check_cancel_input(message.text, message, state):
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

    msg = await message.answer(
        f"✅ Имя изменено на: {text}",
        reply_markup=get_keyboard_for_changing_profile()
    )
    add_message(global_msg_fast, user_id, msg)


async def handle_edit_temp_area(message, state, user_id, bot):
    """Редактирование района через временный профиль."""
    if await check_cancel_input(message.text, message, state):
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

    msg = await message.answer(
        f"✅ Район изменён на: {text}",
        reply_markup=get_keyboard_for_changing_profile()
    )
    add_message(global_msg_fast, user_id, msg)


async def handle_edit_temp_profession(message, state, user_id):
    """Редактирование деятельности через временный профиль."""
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

    msg = await message.answer(
        f"✅ Деятельность изменена на: {text}",
        reply_markup=get_keyboard_for_changing_profile()
    )
    add_message(global_msg_fast, user_id, msg)


async def handle_edit_temp_description(message, state, user_id):
    """Редактирование описания (о себе) через временный профиль."""
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

    msg = await message.answer(
        "✅ Описание о себе обновлено.",
        reply_markup=get_keyboard_for_changing_profile()
    )
    add_message(global_msg_fast, user_id, msg)


async def handle_edit_temp_socials(message, state, user_id):
    """Редактирование ссылок через временный профиль."""
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

    msg = await message.answer(
        "✅ Ссылки обновлены.",
        reply_markup=get_keyboard_for_changing_profile()
    )
    add_message(global_msg_fast, user_id, msg)
