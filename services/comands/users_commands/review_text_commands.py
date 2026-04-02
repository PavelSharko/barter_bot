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

    # 5. Уведомление целевому юзеру о тексте отзыва
    try:
        from services.users_utils.user_profile_manager import load_profiles
        from services.users_utils.all_users_manager import load_all_users
        from entity.Enums_entity import UserProfileFields, UserFields
        import html

        reviews = load_reviews_locked()
        review_id = f"{deal_id}_{user_id}"
        rev_obj = reviews.get(review_id)
        
        target_id = None
        if rev_obj:
            target_id = rev_obj.get("target_user_id")
        
        # Если в объекте нет, падаем на старую логику детекции
        if not target_id:
            from services.users_utils.deals_manager import load_deals_locked
            deals = load_deals_locked()
            deal = deals.get(deal_id)
            if deal:
                client_id = str(deal.get("service_client_id"))
                provider_id = str(deal.get("service_provider_id"))
                target_id = provider_id if str(user_id) == client_id else client_id
                service_name = deal.get("service_name", "услугу")
        else:
            from services.users_utils.deals_manager import load_deals_locked
            deals = load_deals_locked()
            deal = deals.get(deal_id) or {}
            service_name = deal.get("service_name", "услугу")
            
        if target_id:
            profiles = load_profiles()
            users = load_all_users()

            # Кто пишет отзыв?
            reviewer_profile = profiles.get(user_id) or profiles.get(str(user_id)) or {}
            reviewer_name = reviewer_profile.get(UserProfileFields.NAME.value)
            if not reviewer_name:
                reviewer_data = users.get(user_id) or users.get(str(user_id)) or {}
                reviewer_name = reviewer_data.get(UserFields.NAME_REAL.value) or reviewer_data.get(UserFields.NAME_TG.value) or f"ID {user_id}"

            from services.state_bot import global_store
            if global_store.bot:
                await global_store.bot.send_message(
                    chat_id=int(target_id),
                    text=f"📝 Вам оставил текстовый отзыв <b>{html.escape(str(reviewer_name))}</b> за услугу <b>{service_name}</b>:\n\n<i>{text}</i>",
                    parse_mode="HTML"
                )
    except Exception as e:
        import logging
        logging.error(f"Ошибка уведомления о тексте отзыва: {e}")
    
    await clear_waiting_input(state, chat_id, user_id)
