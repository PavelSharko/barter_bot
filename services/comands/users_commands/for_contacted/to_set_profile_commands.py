from handlers.fsm_utils import check_cancel_input, clear_waiting_input
from services.keyboards.keyboards_for_registration import get_area_keyboard
from services.msgs_utils.deleter_messages import clear_messages
from services.state_bot.global_store import global_msg_contacted_fast, add_message, global_msg_fast
from services.users_utils.all_users_manager import load_all_users, save_all_users
from entity.Enums_entity import UserFields
import re


async def extract_and_save_full_name_from_msg(message, state, user_id):
    # проверка что в сообщении есть текст
    text = (message.text or "").strip()
    
    if not text:
        msg = await message.answer("Вы отправили не текст - введите его")
        add_message(global_msg_contacted_fast, user_id, msg)
        return

    # валидация на имя простая что не содержит цифр и спецсимволов
    if len(text) > 100:
        msg = await message.answer("Слишком длинное имя (макс. 100 символов). Попробуйте еще раз.")
        add_message(global_msg_contacted_fast, user_id, msg)
        return
    
    if not re.match(r"^[a-zA-Zа-яА-ЯёЁ\s\-]+$", text):
        msg = await message.answer("Имя должно содержать только буквы, пробелы и дефис. Цифры и спецсимволы запрещены.")
        add_message(global_msg_contacted_fast, user_id, msg)
        return


    # проверка что не отменили ввод команды текста
    if await check_cancel_input(text, message, state):
        return

    # Сохраняем имя
    users = load_all_users()
    if user_id in users:
        users[user_id][UserFields.NAME_REAL.value] = text
        save_all_users()

    await clear_messages(user_id, global_msg_contacted_fast, global_msg_fast)
    msg = await message.answer(
        text=f"✅ Очень приятно, {text}!\n\nТеперь расскажите, с какого вы района?",
        reply_markup=get_area_keyboard()
    )
    add_message(global_msg_contacted_fast, user_id, msg)


    await clear_waiting_input(state, message.chat.id, user_id)