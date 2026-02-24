import logging
from aiogram import Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from datetime import datetime
from filelock import FileLock

from entity.Enums_entity import DealFields, UserMetrics, ReviewFields
from handlers.fsm_utils import set_waiting_input
from services.keyboards.bot_all_buttons import DealProcessButtons, ReviewProcessButtons
from services.keyboards.creator_inline_keyboards import get_review_stars_keyboard, get_add_text_review_keyboard
from services.keyboards.creator_persistent_keyboards import get_cancel_keyboard
from services.msgs_utils.deleter_messages import clear_messages
from services.state_bot.global_store import add_message, global_msg_fast
from services.users_utils.deals_manager import load_deals_locked, save_deals_locked
from services.users_utils.reviews_manager import load_reviews_locked, save_reviews_locked
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
            await bot.send_message(chat_id=user_id, text="Ошибка данных сделки.")
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
                await bot.send_message(chat_id=user_id, text="Ошибка данных сделки при оценке.")
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
                await bot.send_message(chat_id=user_id, text="Сделка не найдена.")
                await call.answer()
                return
                
            if deal.get(DealFields.REVIEW_ALREADY_LEFT.value) == True:
                await bot.send_message(chat_id=user_id, text="Вы уже оставили рейтинг/отзыв.")
                await call.answer()
                return

            deal[DealFields.REVIEW_ALREADY_LEFT.value] = True
            save_deals_locked(deals)

            provider_id = str(deal.get(DealFields.SERVICE_PROVIDER_ID.value))

            # 2.2 Обновляем рейтинг провайдера в all_users.json
            lock = FileLock(f"{config.ALL_USERS_PATH}.lock")
            with lock:
                from services.users_utils.all_users_manager import load_all_users, save_all_users, ALL_USERS_LIST
                users = load_all_users()
                # in all_users.json dict keys are str, but in ALL_USERS_LIST they are int
                prov_id_int = int(provider_id)
                target_user = users.get(prov_id_int)
                if target_user:
                    current_count = target_user.get(UserMetrics.TOTAL_DEALS_COUNT.value, 0)
                    current_sum = target_user.get(UserMetrics.RATING_SUM.value, 0.0)
                    
                    new_count = current_count + 1
                    new_sum = current_sum + stars_count
                    new_avg = round(new_sum / new_count, 2)

                    target_user[UserMetrics.TOTAL_DEALS_COUNT.value] = new_count
                    target_user[UserMetrics.RATING_SUM.value] = new_sum
                    target_user[UserMetrics.RATING_AVG.value] = new_avg
                    
                    ALL_USERS_LIST[prov_id_int] = target_user
                    save_all_users()

            # 2.3 Сохраняем "заготовку" отзыва в reviews.json
            reviews = load_reviews_locked()
            review_id = f"{deal_id}_{user_id}"
            
            reviews[review_id] = {
                ReviewFields.REVIEW_ID.value: review_id,
                ReviewFields.DEAL_ID.value: deal_id,
                ReviewFields.ROLE_IN_DEAL.value: "provider",
                ReviewFields.STARS.value: stars_count,
                ReviewFields.TEXT.value: "", # Текст пока пустой
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
            await call.answer()
            return

    # 3. Нажат "Добавить текст отзыва"
    if data.startswith(f"{ReviewProcessButtons.ADD_TEXT_REVIEW.name.lower()}_"):
        try:
            _, deal_id = data.rsplit('_', 1)
        except ValueError:
            await bot.send_message(chat_id=user_id, text="Ошибка данных.")
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
