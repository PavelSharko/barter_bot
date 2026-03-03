from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from datetime import datetime

from entity.Enums_entity import ReviewFields
from handlers.fsm_utils import clear_waiting_input, check_cancel_input
from services.keyboards.creator_persistent_keyboards import get_persistent_main_menu
from services.msgs_utils.deleter_messages import clear_messages
from services.state_bot.global_store import add_message, global_msg_fast
from services.users_utils.reviews_manager import load_reviews_locked, save_reviews_locked

async def extract_and_save_review_text(message: Message, state: FSMContext, user_id: int):
    """
    Обрабатывает текстовый ввод при добавлении отзыва, валидирует (20-300 симв) и сохраняет в reviews.json.
    """
    chat_id = message.chat.id
    
    # 0. Проверка на отмену
    text_for_cancel = message.text or ""
    if await check_cancel_input(text_for_cancel, message, state):
        await clear_messages(user_id, global_msg_fast)
        return
    
    # 1. Запрет на медиа/стикеры/фото
    if not message.text:
        msg = await message.answer(
            "⚠️ Отзыв — это только текст (можно с эмодзи 😊). Картинки и файлы не принимаются. Напиши словами!"
        )
        add_message(global_msg_fast, user_id, msg)
        add_message(global_msg_fast, user_id, message)
        return

    text = message.text.strip()
    
    # 2. Валидация длины
    if len(text) < 20 or len(text) > 300:
        msg = await message.answer(
            "⚠️ Отзыв должен быть от 20 до 300 символов. Напиши чуть больше или чуть короче — и отправляй!"
        )
        add_message(global_msg_fast, user_id, msg)
        add_message(global_msg_fast, user_id, message) # удалим тоже сам ошибочный текст юзера
        return

    # 2. Получаем ID сделки из State
    state_data = await state.get_data()
    deal_id = state_data.get("current_review_deal_id")
    
    if not deal_id:
        msg = await message.answer("⚠️ Не нашёл привязку к сделке. Нажми кнопку оценки ещё раз — это должно помочь!")
        add_message(global_msg_fast, user_id, msg)
        await clear_waiting_input(state, chat_id, user_id)
        return

    # 3. Обновление reviews.json
    reviews = load_reviews_locked()
    review_id = f"{deal_id}_{user_id}"
    
    if review_id in reviews:
        reviews[review_id][ReviewFields.TEXT.value] = text
        reviews[review_id][ReviewFields.UPDATED_AT.value] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        save_reviews_locked(reviews)
    else:
        # Если почему-то дошли сюда без предсозданного рейтинга, создаем с 0 звезд
        reviews[review_id] = {
            ReviewFields.REVIEW_ID.value: review_id,
            ReviewFields.DEAL_ID.value: deal_id,
            ReviewFields.ROLE_IN_DEAL.value: "provider",
            ReviewFields.STARS.value: 0,
            ReviewFields.TEXT.value: text,
            ReviewFields.CREATED_AT.value: datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            ReviewFields.UPDATED_AT.value: datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        save_reviews_locked(reviews)

    # 4. Успешный ответ и очистка FSM
    add_message(global_msg_fast, user_id, message)
    await clear_messages(user_id, global_msg_fast)
    
    await message.answer("Отзыв сохранён, спасибо! 🎉 Ты помогаешь сообществу.", reply_markup = get_persistent_main_menu())

    
    await clear_waiting_input(state, chat_id, user_id)
