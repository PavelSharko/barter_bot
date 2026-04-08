from aiogram import Bot
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
import html

from services.keyboards.bot_all_buttons import ProcessChangingProfileButtons
from services.keyboards.edit_profile_keyboards import get_keyboard_for_changing_profile, get_services_footer_keyboard, get_service_edit_keyboard
from services.keyboards.creator_persistent_keyboards import get_cancel_keyboard, get_persistent_main_menu
from services.state_bot.global_store import add_message, global_msg_fast
from services.msgs_utils.deleter_messages import clear_messages
from handlers.fsm_utils import set_waiting_input, clear_waiting_input, check_cancel_input
from services.users_utils.temp_profile_manager import get_temp_profile, update_temp_profile
from entity.Enums_entity import UserProfileFields
from initApp.config_loader import config

async def _send_error(message, user_id, text):
    msg = await message.answer(f"❌ {text}")
    add_message(global_msg_fast, user_id, msg)




# ==========================================
# ФАСАД ДЛЯ ДОБАВЛЕНИЯ НОВОЙ УСЛУГИ (3 шага)
# ==========================================
async def facade_add_service_input(message: Message, state: FSMContext, bot: Bot, current_command: str):
    user_id = message.from_user.id
    chat_id = message.chat.id
    text = (message.text or "").strip()

    # --- Проверка отмены ---
    if await check_cancel_input(message.text, message, state):
        await clear_messages(user_id, global_msg_fast)
        await clear_waiting_input(state, chat_id, user_id)
        # Очищаем специфичные переменные рантайма
        await state.update_data(new_service_name=None, new_service_desc=None)

        msg = await bot.send_message(chat_id = user_id, text = "Вы в режиме редактирования профиля",
            reply_markup=get_keyboard_for_changing_profile()
        )
        add_message(global_msg_fast, user_id, msg)
        return

    if not text:
        await _send_error(message, user_id, "Нужен текст — картинки и файлы здесь не подойдут 🙏")
        return

    fsm_data = await state.get_data()

    if current_command == ProcessChangingProfileButtons.ADD_SERVICE_NAME_INPUT.value:
        if not (2 <= len(text) <= 50):
            await _send_error(message, user_id, "Ошибка: название услуги должно быть от 2 до 50 символов")
            return
        
        await clear_messages(user_id, global_msg_fast)
        await clear_waiting_input(state, chat_id, user_id)

        prompt = (
            f"✅ Отлично! Услуга: {html.escape(text)}\n\n"
            "Теперь подробно, но кратко опишите детали услуги (что входит, нюансы).\n"
            "Также укажите условия отмены — за какое время вы готовы принять отмену без последствий.\n\n"
            "⚠️ Пожалуйста, не пишите в этом разделе цену — для неё будет отдельный шаг.\n\n"
            "Описание должно быть от 50 до 300 символов."
        )
        msg = await message.answer(prompt, reply_markup=get_cancel_keyboard())
        add_message(global_msg_fast, user_id, msg)
        await set_waiting_input(state, bot, chat_id, user_id, ProcessChangingProfileButtons.ADD_SERVICE_DESC_INPUT.value, timeout=config.TIME_TO_INPUT_MSG_FSM)
        await state.update_data(new_service_name=text)

    elif current_command == ProcessChangingProfileButtons.ADD_SERVICE_DESC_INPUT.value:
        if not (50 <= len(text) <= 300):
            await _send_error(message, user_id, f"Ошибка: описание должно быть от 50 до 300 символов (сейчас {len(text)})")
            return

        service_name = fsm_data.get("new_service_name", "Услуга")

        await clear_messages(user_id, global_msg_fast)
        await clear_waiting_input(state, chat_id, user_id)

        prompt = (
            f"✅ Описание добавлено!\n\n"
            f"Укажите прайс в долларах целым числом (от 1 до 1000) — 1$ = 1 монета клуба 🪙\n\n"
            f"Цену здесь лучше поставить такую же, как вне клуба, или чуть ниже — но не выше 😊"
        )
        msg = await message.answer(prompt, reply_markup=get_cancel_keyboard())
        add_message(global_msg_fast, user_id, msg)
        await set_waiting_input(state, bot, chat_id, user_id, ProcessChangingProfileButtons.ADD_SERVICE_PRICE_INPUT.value, timeout=config.TIME_TO_INPUT_MSG_FSM)
        await state.update_data(new_service_name=service_name, new_service_desc=text)

    elif current_command == ProcessChangingProfileButtons.ADD_SERVICE_PRICE_INPUT.value:
        if not text.isdigit():
            await _send_error(message, user_id, "Ошибка: цена должна быть целым числом")
            return

        price_val = int(text)
        if not (1 <= price_val <= 1000):
            await _send_error(message, user_id, "Ошибка: цена услуги должна быть от 1 до 1000 монет")
            return

        service_name = fsm_data.get("new_service_name", "Услуга")
        service_desc = fsm_data.get("new_service_desc", "")

        temp = get_temp_profile(user_id) or {}
        services = temp.get(UserProfileFields.SERVICES.value, [])
        services.append({
            'name': service_name,
            'description': service_desc,
            'price': text
        })
        update_temp_profile(user_id, {UserProfileFields.SERVICES.value: services})

        await clear_messages(user_id, global_msg_fast)
        await clear_waiting_input(state, chat_id, user_id)

        await message.answer(
            f"...: {text}",
            reply_markup=get_persistent_main_menu()
        )   
        msg = await message.answer(
            "✅ Услуга добавлена!",
            reply_markup=get_keyboard_for_changing_profile()
        )
        add_message(global_msg_fast, user_id, msg)


# ==========================================
# ФАСАД ДЛЯ РЕДАКТИРОВАНИЯ УСЛУГИ (3 шага)
# ==========================================
async def facade_edit_service_input(message: Message, state: FSMContext, bot: Bot, current_command: str):
    user_id = message.from_user.id
    chat_id = message.chat.id
    text = (message.text or "").strip()

    # --- Проверка отмены ---
    if await check_cancel_input(message.text, message, state):
        await clear_messages(user_id, global_msg_fast)
        await clear_waiting_input(state, chat_id, user_id)
        # Очищаем специфичные переменные рантайма
        await state.update_data(editing_service_idx=None, editing_service_name=None, editing_service_desc=None)

        msg = await bot.send_message(chat_id = user_id, text = "Вы в режиме редактирования профиля",
            reply_markup=get_keyboard_for_changing_profile()
        )
        add_message(global_msg_fast, user_id, msg)
        return

    if not text:
        await _send_error(message, user_id, "Нужен текст — картинки и файлы здесь не подойдут 🙏")
        return

    fsm_data = await state.get_data()
    service_idx = fsm_data.get("editing_service_idx", 0)

    if current_command == ProcessChangingProfileButtons.EDIT_SERVICE_NAME_INPUT.value:
        if not (2 <= len(text) <= 50):
            await _send_error(message, user_id, "Ошибка: название услуги должно быть от 2 до 50 символов")
            return

        temp = get_temp_profile(user_id) or {}
        services = temp.get(UserProfileFields.SERVICES.value, [])
        old_desc = "Нет описания"
        if service_idx < len(services):
            old_desc = html.escape(str(services[service_idx].get('description', 'Нет описания')))

        await clear_messages(user_id, global_msg_fast)
        await clear_waiting_input(state, chat_id, user_id)

        prompt = (
            f"✅ Супер — название изменено!\n\n"
            f"Теперь введите описание услуги.\n"
            f"Ранее услуга описывалась так:\n<i>{old_desc}</i>\n\n"
            f"Введите новое описание (от 50 до 300 символов):"
        )
        msg = await message.answer(prompt, parse_mode="HTML", reply_markup=get_cancel_keyboard())
        add_message(global_msg_fast, user_id, msg)
        await set_waiting_input(state, bot, chat_id, user_id, ProcessChangingProfileButtons.EDIT_SERVICE_DESC_INPUT.value, timeout=config.TIME_TO_INPUT_MSG_FSM)
        await state.update_data(editing_service_idx=service_idx, editing_service_name=text)

    elif current_command == ProcessChangingProfileButtons.EDIT_SERVICE_DESC_INPUT.value:
        if not (50 <= len(text) <= 300):
            await _send_error(message, user_id, f"Ошибка: описание должно быть от 50 до 300 символов (сейчас {len(text)})")
            return

        editing_service_name = fsm_data.get("editing_service_name", "Услуга")

        await clear_messages(user_id, global_msg_fast)
        await clear_waiting_input(state, chat_id, user_id)

        prompt = (
            f"✅ Описание сохранено!\n\n"
            f"Теперь введите цену услуги в долларах (целое число от 1 до 1000).\n"
            f"1$ = 1 монета клуба 🪙"
        )
        msg = await message.answer(prompt, reply_markup=get_cancel_keyboard())
        add_message(global_msg_fast, user_id, msg)
        await set_waiting_input(state, bot, chat_id, user_id, ProcessChangingProfileButtons.EDIT_SERVICE_PRICE_INPUT.value, timeout=config.TIME_TO_INPUT_MSG_FSM)
        await state.update_data(
            editing_service_idx=service_idx,
            editing_service_name=editing_service_name,
            editing_service_desc=text
        )

    elif current_command == ProcessChangingProfileButtons.EDIT_SERVICE_PRICE_INPUT.value:
        if not text.isdigit():
            await _send_error(message, user_id, "Ошибка: цена должна быть целым числом")
            return

        price_val = int(text)
        if not (1 <= price_val <= 1000):
            await _send_error(message, user_id, "Ошибка: цена услуги должна быть от 1 до 1000 монет")
            return

        editing_service_name = fsm_data.get("editing_service_name", "Услуга")
        editing_service_desc = fsm_data.get("editing_service_desc", "Описание")

        temp = get_temp_profile(user_id) or {}
        services = temp.get(UserProfileFields.SERVICES.value, [])
        if service_idx < len(services):
            services[service_idx]['name'] = editing_service_name
            services[service_idx]['description'] = editing_service_desc
            services[service_idx]['price'] = text
            update_temp_profile(user_id, {UserProfileFields.SERVICES.value: services})

        await clear_messages(user_id, global_msg_fast)
        await clear_waiting_input(state, chat_id, user_id)

        await message.answer(
            f"...: {text}",
            reply_markup=get_persistent_main_menu()
        )
        msg = await message.answer(
            "Отлично, услуга была изменена ✅",
            reply_markup=get_keyboard_for_changing_profile()
        )
        add_message(global_msg_fast, user_id, msg)
