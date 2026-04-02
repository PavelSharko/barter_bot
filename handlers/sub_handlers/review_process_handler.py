import logging
import html
from aiogram import Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from datetime import datetime
from filelock import FileLock

from entity.Enums_entity import DealFields, UserMetrics, ReviewFields, UserFields, UserProfileFields
from handlers.fsm_utils import set_waiting_input
from services.keyboards.bot_all_buttons import DealProcessButtons, ReviewProcessButtons
from services.keyboards.creator_inline_keyboards import get_review_stars_keyboard, get_add_text_review_keyboard
from services.keyboards.creator_persistent_keyboards import get_cancel_keyboard
from services.msgs_utils.deleter_messages import clear_messages
from services.state_bot.global_store import add_message, global_msg_fast
from services.users_utils.deals_manager import load_deals_locked, save_deals_locked
from services.users_utils.reviews_manager import load_reviews_locked, save_reviews_locked
from services.users_utils.user_profile_manager import load_profiles
from services.users_utils.all_users_manager import load_all_users, save_all_users, ALL_USERS_LIST
from initApp.config_loader import config

async def handle_review_callbacks(call: CallbackQuery, bot: Bot, state: FSMContext):
    """Шлюз для обработки кнопок начала рейтинга, выбора звезд и ввода текста отзыва."""
    data = call.data
    user_id = call.from_user.id
    chat_id = call.message.chat.id

    # 1. По нажатию на "Оставить отзыв" / "Написать отзыв" (открывает звездочки)
    if data.startswith(f"{DealProcessButtons.LEAVE_REVIEW.name.lower()}_") or \
       data.startswith(f"{DealProcessButtons.LEAVE_REVIEW_CLIENT.name.lower()}_"):
        
        try:
            _, deal_id = data.rsplit('_', 1)
        except ValueError:
            await bot.send_message(chat_id=user_id, text="⚠️ Ошибка — попробуй нажать кнопку ещё раз.")
            await call.answer()
            return
            
        await clear_messages(user_id, global_msg_fast)
        
        # Удаляем эту сказочную кнопку (и вообще клавиатуру) из сообщения, на которое нажали
        try:
            await call.message.edit_reply_markup(reply_markup=None)
        except Exception:
            pass
        
        # Можно тут проверить, не оставлен ли уже отзыв, но пока просто даем клавиатуру
        msg = await bot.send_message(
            chat_id=user_id,
            text="Оставьте рейтинг участнику",
            reply_markup=get_review_stars_keyboard(deal_id)
        )
        add_message(global_msg_fast, user_id, msg)
        await call.answer()
        return

    # 2. По нажатию на любую из 5 звезд
    for star_btn in [
        ReviewProcessButtons.STAR_1, 
        ReviewProcessButtons.STAR_2, 
        ReviewProcessButtons.STAR_3, 
        ReviewProcessButtons.STAR_4, 
        ReviewProcessButtons.STAR_5
    ]:
        if data.startswith(f"{star_btn.name.lower()}_"):
            try:
                _, deal_id = data.rsplit('_', 1)
            except ValueError:
                await bot.send_message(chat_id=user_id, text="⚠️ Ошибка — попробуй нажать кнопку ещё раз.")
                await call.answer()
                return
                
            # Удаляем звездочки с пред. сообщения
            try:
                await call.message.edit_reply_markup(reply_markup=None)
            except Exception:
                pass

            stars_count = int(star_btn.value[0]) # Парсим '1', '2' и т.д. из '1⭐️'

            # 2.1 Обновляем статус сделки
            deals = load_deals_locked()
            deal = deals.get(deal_id)
            if not deal:
                await bot.send_message(chat_id=user_id, text="❌ Сделка не найдена — возможно, она уже устарела.")
                await call.answer()
                return
                
            # 2.2 Определяем роли и целевого юзера
            client_id = str(deal.get(DealFields.SERVICE_CLIENT_ID.value))
            provider_id = str(deal.get(DealFields.SERVICE_PROVIDER_ID.value))
            
            profiles = load_profiles()
            users = load_all_users()

            # Кто пишет отзыв?
            reviewer_profile = profiles.get(user_id) or profiles.get(str(user_id)) or {}
            reviewer_name = reviewer_profile.get(UserProfileFields.NAME.value)
            if not reviewer_name:
                reviewer_data = users.get(user_id) or users.get(str(user_id)) or {}
                reviewer_name = reviewer_data.get(UserFields.NAME_REAL.value) or reviewer_data.get(UserFields.NAME_TG.value) or f"ID {user_id}"

            if str(user_id) == client_id:
                reviewer_role = "client"
                target_id = provider_id
            else:
                reviewer_role = "provider"
                target_id = client_id

            # 2.3 Проверяем, не оставлен ли уже отзыв ЭТИМ юзером для ЭТОЙ сделки
            # Ключ: {deal_id}_{от_кого}
            review_key = f"{deal_id}_{user_id}"
            reviews = load_reviews_locked()
            if review_key in reviews:
                  await bot.send_message(chat_id=user_id, text="Вы уже оставили рейтинг/отзыв для этой сделки.")
                  await call.answer()
                  return

            # 2.4 Обновляем рейтинг целевого юзера (того, КОМУ оставили отзыв) в all_users.json
            lock = FileLock(f"{config.ALL_USERS_PATH}.lock")
            with lock:
                users = load_all_users()
                target_id_int = int(target_id)
                target_user = users.get(target_id_int)
                if target_user:
                    current_count = target_user.get(UserMetrics.TOTAL_DEALS_COUNT.value, 0)
                    current_sum = target_user.get(UserMetrics.RATING_SUM.value, 0.0)
                    
                    new_count = current_count + 1
                    new_sum = current_sum + stars_count
                    new_avg = round(new_sum / new_count, 2)

                    target_user[UserMetrics.TOTAL_DEALS_COUNT.value] = new_count
                    target_user[UserMetrics.RATING_SUM.value] = new_sum
                    target_user[UserMetrics.RATING_AVG.value] = new_avg
                    
                    ALL_USERS_LIST[target_id_int] = target_user
                    save_all_users()

            # 2.5 Сохраняем отзыв в reviews.json
            # review_id = ключ в базе
            reviews[review_key] = {
                ReviewFields.REVIEW_ID.value: review_key,
                ReviewFields.DEAL_ID.value: deal_id,
                "target_user_id": str(target_id), # Тот, о ком отзыв (владелец профиля)
                "reviewer_id": str(user_id),      # Тот, кто написал
                ReviewFields.ROLE_IN_DEAL.value: reviewer_role, # Роль автора (Заказчик/Исполнитель)
                ReviewFields.STARS.value: stars_count,
                ReviewFields.TEXT.value: "", 
                ReviewFields.CREATED_AT.value: datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                ReviewFields.UPDATED_AT.value: datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            save_reviews_locked(reviews)

            # 2.4 Ответ пользователю
            await clear_messages(user_id, global_msg_fast)
            msg = await bot.send_message(
                chat_id=user_id,
                text="Рейтинг пользователя обновлен - ваши звезды учтены ⭐️ \n\nДобавьте текст отзыва",
                reply_markup=get_add_text_review_keyboard(deal_id)
            )
            add_message(global_msg_fast, user_id, msg)

            # 2.6 Уведомление целевому юзеру о звездах
            try:
                service_name = deal.get(DealFields.SERVICE_NAME.value, "услугу")
                await bot.send_message(
                    chat_id=int(target_id),
                    text=f"⭐️ Вам поставил оценку <b>{html.escape(str(reviewer_name))}</b> {stars_count} звезд за услугу <b>{service_name}</b>!",
                    parse_mode="HTML"
                )
            except Exception as e:
                logging.error(f"Ошибка уведомления о звездах: {e}")

            await call.answer()
            return

    # 3. Нажат "Добавить текст отзыва"
    if data.startswith(f"{ReviewProcessButtons.ADD_TEXT_REVIEW.name.lower()}_"):
        try:
            _, deal_id = data.rsplit('_', 1)
        except ValueError:
            await bot.send_message(chat_id=user_id, text="⚠️ Ошибка — попробуй нажать кнопку ещё раз.")
            await call.answer()
            return
            
        await clear_messages(user_id, global_msg_fast)
        
        # Удаляем кнопку 'добавить текст'
        try:
            await call.message.edit_reply_markup(reply_markup=None)
        except Exception:
            pass
        
        # Переводим бота в состояние ожидания (ЭТО СБРАСЫВАЕТ ВСЕ ДАННЫЕ FSM)
        await set_waiting_input(state, bot, chat_id, user_id, ReviewProcessButtons.ADD_TEXT_REVIEW.name.lower(), timeout=config.TIME_TO_INPUT_MSG_FSM)
        
        # Сохраним deal_id в state, чтобы text_handler знал, к какой сделке этот отзыв
        await state.update_data(current_review_deal_id=deal_id)
        
        msg = await bot.send_message(
            chat_id=user_id,
            text="✏️ Напишите ваш отзыв (длина от 20 до 300 символов, можно использовать текст и эмодзи):",
            reply_markup=get_cancel_keyboard()
        )
        add_message(global_msg_fast, user_id, msg)
        await call.answer()
        return
