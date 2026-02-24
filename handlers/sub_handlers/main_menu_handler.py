from aiogram import Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from datetime import datetime
import time
import html

from filelock import FileLock
from initApp.config_loader import config
from services.keyboards.bot_all_buttons import MainMenuButtons
from services.keyboards.creator_persistent_keyboards import get_persistent_main_menu
from services.msgs_utils.deleter_messages import clear_messages
from services.state_bot.global_store import global_msg_fast, add_message
from services.users_utils.user_profile_manager import load_profiles
from services.users_utils.deals_manager import load_deals_locked, save_deals_locked
from entity.Enums_entity import UserProfileFields, UserMetrics, UserFields, UserLifecycleStatus, DealStatus, DealFields
from services.keyboards.creator_inline_keyboards import get_profile_view_keyboard, get_find_service_keyboard, get_service_profile_keyboard, get_accept_terms_keyboard, get_reviews_list_keyboard
from services.comands.users_commands.show_balance import show_user_balance
from services.users_utils.all_users_manager import load_all_users, save_all_users
from services.users_utils.reviews_manager import load_reviews_locked
from services.keyboards.sustem_inline_keyboard import get_inline_keyboard_close

async def handle_callback_main_menu_for_users(call: CallbackQuery, bot: Bot, state: FSMContext):
    """
    Обработчик callback-кнопок главного меню пользователя.
    """
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    data = call.data
    await clear_messages(user_id, global_msg_fast)

    # 1. Посмотреть свой профиль
    if data == MainMenuButtons.VIEW_PROFILE.name.lower():
        await clear_messages(user_id, global_msg_fast)
        
        await call.answer()
        
        profiles = load_profiles()
        user_profile = profiles.get(user_id) or profiles.get(str(user_id))
        
        if not user_profile:
             msg = await call.message.answer("⚠️ Профиль не найден.")
             add_message(global_msg_fast, user_id, msg)
             return

        text = (
            f"👤 **Ваш профиль:**\n\n"
            f"**Имя:** {user_profile.get(UserProfileFields.NAME.value, 'Не указано')}\n"
            f"**Район:** {user_profile.get(UserProfileFields.AREA.value, 'Не указано')}\n"
            f"**Услуга/Товар:** {user_profile.get(UserProfileFields.SERVICE_NAME.value, 'Не указано')}\n"
            f"**Описание:** {user_profile.get(UserProfileFields.SERVICE_DESCRIPTION.value, 'Не указано')}\n"
            f"**Прайс:** {user_profile.get(UserProfileFields.PRICE_INFO.value, 'Не указано')}\n"
        )
        
        msg = await call.message.answer(
            text,
            reply_markup=get_profile_view_keyboard(),
            parse_mode="Markdown"
        )
        add_message(global_msg_fast, user_id, msg)
        return

    # 2. Мой баланс
    elif data == MainMenuButtons.VIEW_MY_BALANCE.name.lower():
        await show_user_balance(call, bot) 
        return

    # 3. Баланс других
    elif data == MainMenuButtons.VIEW_OTHERS_BALANCE.name.lower():
        await call.answer()
        
        users = load_all_users()
        profiles = load_profiles()
        
        total_balance = 0
        user_balances = []
        
        for u_id, u_data in users.items():
            balance = u_data.get(UserMetrics.BALANCE.value, 0)
            total_balance += balance
            
            if balance == 0:
                continue
                
            # Попытка получить имя из профиля, если его нет - берём из users
            u_profile = profiles.get(u_id) or profiles.get(str(u_id)) or {}
            name = u_profile.get(UserProfileFields.NAME.value)
            if not name:
                name = u_data.get(UserFields.NAME_REAL.value) or u_data.get(UserFields.NAME_TG.value) or f"ID{u_id}"
                
            user_balances.append((name, balance))
            
        user_balances.sort(key=lambda x: x[1], reverse=True)
        
        text = f"<b>ОБЩИЙ БАЛАНС МОНЕТ В КЛУБЕ 🪙 - {total_balance:g}</b>\n\n"
        for name, balance in user_balances:
            text += f"- {html.escape(str(name))} - {balance:g} монет\n"
            
        msg = await call.message.answer(
            text, 
            parse_mode="HTML",
            reply_markup=get_inline_keyboard_close()
        )
        

        add_message(global_msg_fast, user_id, msg)
        return

    # 4. История сделок
    elif data == MainMenuButtons.VIEW_DEALS_HISTORY.name.lower():
        await call.answer()
        
        deals = load_deals_locked()
        str_user_id = str(user_id)
        
        user_deals = []
        for d_id, deal in deals.items():
            s_client = str(deal.get(DealFields.SERVICE_CLIENT_ID.value, ""))
            s_provider = str(deal.get(DealFields.SERVICE_PROVIDER_ID.value, ""))
            if str_user_id == s_client or str_user_id == s_provider:
                user_deals.append((d_id, deal))
                
        if not user_deals:
            msg = await call.message.answer("У вас нет истории сделок.", reply_markup=get_inline_keyboard_close())
            add_message(global_msg_fast, user_id, msg)
            return
            
        # сортируем по дате создания убыванию
        user_deals.sort(key=lambda x: str(x[1].get(DealFields.CREATED_AT.value, "")), reverse=True)
        
        status_map = {
            DealStatus.PENDING_CONFIRMATION.value: "🟡 Ожидает подтверждения",
            DealStatus.IN_PROGRESS.value: "🔵 В процессе",
            DealStatus.FINISHED.value: "🟢 Завершена",
            DealStatus.CANCELLED.value: "🔴 Отменена"
        }
        
        chunks = [user_deals[i:i + 3] for i in range(0, len(user_deals), 3)]
        
        for i, chunk in enumerate(chunks):
            response_texts = []
            for d_id, deal in chunk:
                service_name = html.escape(str(deal.get(DealFields.SERVICE_NAME.value, "Услуга")))
                price = deal.get(DealFields.PRICE_IN_COINS.value, 0)
                status_raw = deal.get(DealFields.STATUS_DEAL.value, "")
                status_ru = status_map.get(status_raw, status_raw)
                created_at = deal.get(DealFields.CREATED_AT.value, "Неизвестно")
                
                s_client = str(deal.get(DealFields.SERVICE_CLIENT_ID.value, ""))
                if str_user_id == s_client:
                    role_str = "заказчик"
                else:
                    role_str = "исполнитель"
                    
                text = (
                    f"<b>Название услуги:</b> <u>{service_name}</u>\n"
                    f"Вы в качестве: <i>{role_str}</i>\n"
                    f"<b>Статус сделки:</b> {status_ru}\n"
                    f"<b>Стоимость услуги:</b> {price} 🪙\n"
                    f"<b>Дата:</b> {created_at}\n"
                )
                response_texts.append(text)
                
            final_text = "\n\n---\n\n".join(response_texts)
            
            # Клавиатуру добавляем только к последнему сообщению
            reply_markup = get_inline_keyboard_close() if i == len(chunks) - 1 else None
            
            msg = await call.message.answer(text=final_text, parse_mode="HTML", reply_markup=reply_markup)
            add_message(global_msg_fast, user_id, msg)
            
        return



    # 5. Найти услугу/товар & Возврат назад
    elif data in (MainMenuButtons.FIND_SERVICE.name.lower(), MainMenuButtons.BACK_TO_SERVICES.name.lower()):
        await call.answer()
        
        msg = await call.message.answer(
            "Вот список доступных услуг на острове Бали:", 
            reply_markup=get_find_service_keyboard()
        )
        add_message(global_msg_fast, user_id, msg)
        return

    # 5.1 Нажатие на конкретную услугу из списка "Найти услугу/товар" (ищем профиль)
    elif data.startswith(f"{MainMenuButtons.FIND_SERVICE.name.lower()}_"):
        await call.answer()
        # Парсим ID из строки `find_service_ID`
        try:
            _, target_id_str = data.rsplit('_', 1)
            target_id = int(target_id_str)
        except Exception:
            return
            
        profiles = load_profiles()
        target_profile = profiles.get(target_id) or profiles.get(str(target_id))
        
        if not target_profile:
             msg = await call.message.answer("⚠️ Профиль этого пользователя не найден.")
             add_message(global_msg_fast, user_id, msg)
             return
             
        text = (
            f"👤 <b>Профиль услуги:</b>\n\n"
            f"<b>Имя:</b> {html.escape(str(target_profile.get(UserProfileFields.NAME.value, 'Не указано')))}\n"
            f"<b>Район:</b> {html.escape(str(target_profile.get(UserProfileFields.AREA.value, 'Не указано')))}\n"
            f"<b>Услуга/Товар:</b> {html.escape(str(target_profile.get(UserProfileFields.SERVICE_NAME.value, 'Не указано')))}\n"
            f"<b>Описание:</b> {html.escape(str(target_profile.get(UserProfileFields.SERVICE_DESCRIPTION.value, 'Не указано')))}\n"
            f"<b>Прайс:</b> {html.escape(str(target_profile.get(UserProfileFields.PRICE_INFO.value, 'Не указано')))}\n"
        )
            
        msg = await call.message.answer(
            text,
            reply_markup=get_service_profile_keyboard(target_id_str),
            parse_mode="HTML"
        )
        add_message(global_msg_fast, user_id, msg)
        return

    # 5.2 Просмотр отзывов чужого профиля
    elif data.startswith(f"{MainMenuButtons.REVIEWS.name.lower()}_"):
        await call.answer()
        try:
            _, target_id_str = data.rsplit('_', 1)
        except Exception:
            return
            
        await clear_messages(user_id, global_msg_fast)
        
        target_reviews = []
        try:
            reviews_db = load_reviews_locked()
            for r_id, r_data in reviews_db.items():
                if r_id.endswith(f"_{target_id_str}"):
                    target_reviews.append(r_data)
        except Exception as e:
            msg = await call.message.answer("⚠️ Не удалось загрузить отзывы.")
            add_message(global_msg_fast, user_id, msg)
            return

        if not target_reviews:
            msg = await call.message.answer(
                "У этого пользователя пока нет отзывов. 📭",
                reply_markup=get_inline_keyboard_close()
            )
            add_message(global_msg_fast, user_id, msg)
            return

        # Сортировка по убыванию даты (самые свежие сверху)
        target_reviews.sort(key=lambda x: str(x.get("created_at", "")), reverse=True)
        top_5_reviews = target_reviews[:5]

        # Приветственное сообщение
        msg = await call.message.answer("📝 <b>Вот последние отзывы об этом пользователе:</b>", parse_mode="HTML")
        add_message(global_msg_fast, user_id, msg)

        # Отправка самих отзывов
        for idx, r in enumerate(top_5_reviews):
            stars_num = int(r.get("stars", 0))
            stars_str = "⭐" * stars_num + "⚫️" * (5 - stars_num)
            
            role = r.get("role_in_deal", "unknown")
            role_ru = "Исполнитель" if role == "provider" else "Заказчик" if role == "client" else role
            
            text_review = r.get("text", "Без текста")
            created_at = r.get("created_at", "Неизвестна")
            
            formatted_text = (
                f"<b>Роль в сделке:</b> {role_ru}\n"
                f"<b>Оценка:</b> {stars_str}\n"
                f"<b>Дата:</b> {created_at}\n\n"
                f"💬 <i>{text_review}</i>"
            )
            
            # К последнему отзыву цепляем кнопку 'Закрыть и назад к списку'
            reply_markup = get_reviews_list_keyboard() if idx == len(top_5_reviews) - 1 else None
            
            msg = await call.message.answer(
                text=formatted_text,
                parse_mode="HTML",
                reply_markup=reply_markup
            )
            add_message(global_msg_fast, user_id, msg)
            
        return

    # 5.3 Создание сделки с чужим профилем -> Выдача условий
    elif data.startswith(f"{MainMenuButtons.CREATE_DEAL.name.lower()}_"):
        await call.answer()
        try:
            _, target_id_str = data.rsplit('_', 1)
            target_id = int(target_id_str)
        except Exception:
            return
            
        if user_id == target_id:
            msg = await call.message.answer(
                "Вы не можете создать сделку с самим собой!",
                reply_markup=get_inline_keyboard_close()
            )
            add_message(global_msg_fast, user_id, msg)
            return
            
        msg = await call.message.answer(
            "вы принимаете условиями оказания и отмены услуги которую выбираете?",
            reply_markup=get_accept_terms_keyboard(target_id_str)
        )
        add_message(global_msg_fast, user_id, msg)
        return

    # 5.4 Принятие условий сделки
    elif data.startswith(f"{MainMenuButtons.ACCEPT_TERMS.name.lower()}_"):
        await call.answer()
        try:
            _, provider_id_str = data.rsplit('_', 1)
            provider_id = int(provider_id_str)
        except Exception:
            return
            
        if user_id == provider_id:
            msg = await call.message.answer(
                "Вы не можете создать сделку с самим собой!",
                reply_markup=get_inline_keyboard_close()
            )
            add_message(global_msg_fast, user_id, msg)
            return
            
        # Загружаем юзеров для проверки баланса
        lock = FileLock(f"{config.ALL_USERS_PATH}.lock")
        with lock:
            users = load_all_users()
            buyer_data = users.get(user_id)
            if not buyer_data:
                return
                
            total_balance = float(buyer_data.get(UserMetrics.BALANCE.value, 0))
            block_balance = float(buyer_data.get(UserMetrics.BLOCK_BALANCE.value, 0))
            free_balance = total_balance - block_balance
            
            # Получаем профиль исполнителя для цены
            profiles = load_profiles()
            provider_profile = profiles.get(provider_id) or profiles.get(str(provider_id))
            
            if not provider_profile:
                msg = await call.message.answer("⚠️ Профиль этого пользователя не найден.")
                add_message(global_msg_fast, user_id, msg)
                return
                
            try:
                price = float(provider_profile.get(UserProfileFields.PRICE_INFO.value, 0))
            except ValueError:
                price = 0.0
                
            
            required_amount = round(price * 1.1, 2)
            
            # Проверка на наличие уже открытой сделки
            deals = load_deals_locked()
            for existing_deal in deals.values():
                if (existing_deal.get(DealFields.SERVICE_CLIENT_ID.value) == user_id and 
                    existing_deal.get(DealFields.SERVICE_PROVIDER_ID.value) == provider_id and
                    existing_deal.get(DealFields.STATUS_DEAL.value) in (DealStatus.PENDING_CONFIRMATION.value, DealStatus.IN_PROGRESS.value)):
                    
                    msg = await call.message.answer(
                        "У вас уже есть активная заявка к этому пользователю. Дождитесь подтверждения!",
                        reply_markup=get_inline_keyboard_close()
                    )
                    add_message(global_msg_fast, user_id, msg)
                    return
            
            if free_balance < required_amount:
                msg = await call.message.answer(
                    f"<b>У вас не хватает монет чтобы записаться на услугу!</b>\n"
                    f"Ваше общее количество монет = <b>{total_balance:g}</b>\n"
                    f"Заблокировано в других сделках = <b>{block_balance:g}</b>\n"
                    f"Свободные монеты = <b>{free_balance:g}</b>\n"
                    f"Требуется = <b>{required_amount:g}</b>",
                    reply_markup=get_inline_keyboard_close(),
                    parse_mode="HTML"
                )
                add_message(global_msg_fast, user_id, msg)
                return

            # Блокируем средства
            buyer_data[UserMetrics.BLOCK_BALANCE.value] = round(block_balance + required_amount, 2)
            from services.users_utils.all_users_manager import ALL_USERS_LIST
            ALL_USERS_LIST.clear()
            ALL_USERS_LIST.update(users)
            save_all_users()
        
        # Создаем сделку
        deal_id = f"{user_id}{int(time.time())}"
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        deal_data = {
            DealFields.DEAL_ID.value: deal_id,
            DealFields.CREATED_AT.value: current_time,
            DealFields.UPDATED_AT.value: current_time,
            DealFields.SERVICE_PROVIDER_ID.value: provider_id,
            DealFields.SERVICE_CLIENT_ID.value: user_id,
            DealFields.SERVICE_NAME.value: provider_profile.get(UserProfileFields.SERVICE_NAME.value, "Не указано"),
            DealFields.PRICE_IN_COINS.value: price,
            DealFields.STATUS_DEAL.value: DealStatus.PENDING_CONFIRMATION.value,
            DealFields.DATA_CONFIRMED_AT.value: None,
            DealFields.DATA_CANCELLED_AT.value: None,
            DealFields.REVIEW_ALREADY_LEFT.value: False
        }
        
        deals = load_deals_locked()
        deals[deal_id] = deal_data
        save_deals_locked(deals)
        
        service_name = deal_data[DealFields.SERVICE_NAME.value]
        
        msg = await call.message.answer(
            f"Сделка создана, {required_amount} монет(ы) заблокировано до оказания услуги или отмены.\n\n Пользователь, который предоставляет услугу <b>{service_name}</b>, получил ваш запрос и как только он подтвердит запрос, вы получите контакты друг друга.",
            reply_markup=get_inline_keyboard_close(),
            parse_mode="HTML"
        )
        add_message(global_msg_fast, user_id, msg)
        
        # Уведомляем исполнителя
        from services.keyboards.creator_inline_keyboards import get_provider_deal_action_keyboard
        try:
            profiles = load_profiles()
            buyer_profile = profiles.get(user_id) or profiles.get(str(user_id)) or {}
            buyer_name = buyer_profile.get(UserProfileFields.NAME.value)
            
            if not buyer_name:
                users_dict = load_all_users()
                b_data = users_dict.get(user_id) or users_dict.get(str(user_id)) or {}
                buyer_name = b_data.get(UserFields.NAME_REAL.value) or b_data.get(UserFields.NAME_TG.value) or f"ID {user_id}"

            notify_text = (
                f"Вам поступила новая заявка на услугу <b>{html.escape(str(deal_data[DealFields.SERVICE_NAME.value]))}</b>\n"
                f"От клиента <b>{html.escape(str(buyer_name))}</b>\n\n"
                f"Для того чтобы договорится с клиентом об услуге нажмите {MainMenuButtons.ACCEPT_REQUEST.value}:\n\n"
                f"После оказания услуги вы получите {price:}  монет."
            )
            msg_prov = await bot.send_message(
                chat_id=provider_id,
                text=notify_text,
                parse_mode="HTML",
                reply_markup=get_provider_deal_action_keyboard(deal_id)
            )
        except Exception as e:
            print(f"Ошибка отправки уведомления исполнителю: {e}")
            
        # Уведомляем модератора
        try:
            moderator_text = (
                f"⚠️ <b>Создана новая сделка</b> ⚠️\n"
                f"ID Сделки: <code>{deal_id}</code>\n"
                f"Клиент: <code>{user_id}</code>\n"
                f"Исполнитель: <code>{provider_id}</code>\n"
                f"Услуга: {html.escape(str(deal_data[DealFields.SERVICE_NAME.value]))}\n"
                f"Сумма: {price:g} монет."
            )
            msg_mod = await bot.send_message(
                chat_id=config.MODERATOR_CONTACT_ID,
                text=moderator_text,
                parse_mode="HTML"
            )
        except Exception as e:
            print(f"Ошибка отправки уведомления модератору: {e}")
            
        return

    # 6. CONFIRM_DEAL = "Активные сделки ✅" переход в подменю
    elif data == MainMenuButtons.CONFIRM_DEAL.name.lower():
        await call.answer("Сейчас покажу 😉")
        await clear_messages(call.from_user.id, global_msg_fast)
        deals = load_deals_locked()
        profiles = load_profiles()
        # Получаем сделки, где юзер - клиент
        client_deals = []
        for d in deals.values():
            if d.get(DealFields.SERVICE_CLIENT_ID.value) == user_id and d.get(DealFields.STATUS_DEAL.value) in [DealStatus.PENDING_CONFIRMATION.value, DealStatus.IN_PROGRESS.value]:
                client_deals.append(d)
                
        # Получаем сделки, где юзер - исполнитель
        provider_deals = []
        for d in deals.values():
            if d.get(DealFields.SERVICE_PROVIDER_ID.value) == user_id and d.get(DealFields.STATUS_DEAL.value) == DealStatus.IN_PROGRESS.value:
                provider_deals.append(d)
                
        def format_deal_msg(deal_data, other_user_name, is_client: bool):
            deal_id = deal_data.get(DealFields.DEAL_ID.value, "Неизвестно")
            service = html.escape(str(deal_data.get(DealFields.SERVICE_NAME.value, "Неизвестная услуга")))
            price = deal_data.get(DealFields.PRICE_IN_COINS.value, 0)
            status = deal_data.get(DealFields.STATUS_DEAL.value, "")
            
            # Подстановка статуса на русском
            if status == DealStatus.PENDING_CONFIRMATION.value:
                status_ru = "⏳ Ожидает подтверждения"
            elif status == DealStatus.IN_PROGRESS.value:
                status_ru = "🔄 В процессе выполнения"
            else:
                status_ru = status
                
            role_text = "Исполнитель:" if is_client else "Клиент:"
            clean_name = html.escape(str(other_user_name))
            
            return (
                f"ID Сделки: <code>{deal_id}</code>\n"
                f"Услуга: <b>{service}</b>\n"
                f"Сумма: <b>{price:g}</b>\n"
                f"{role_text} <b>{clean_name}</b>\n"
                f"Статус: {status_ru}\n\n"
                f""
                f"!Важно - не нажимайте ✅Услуга оказана - пока вы не получили услугу - потому что монеты у вас будут сразу списаны"
            )

        from services.keyboards.creator_inline_keyboards import get_client_deal_keyboard, get_provider_deal_keyboard

        if client_deals:
            msg = await call.message.answer("список сделок на которые вы записались как клиент 😎")
            add_message(global_msg_fast, user_id, msg)
            for deal in client_deals:
                p_id = deal.get(DealFields.SERVICE_PROVIDER_ID.value)
                p_profile = profiles.get(p_id) or profiles.get(str(p_id)) or {}
                p_name = p_profile.get(UserProfileFields.NAME.value) or f"ID {p_id}"
                
                deal_id = deal.get(DealFields.DEAL_ID.value)
                text_msg = format_deal_msg(deal, p_name, True)
                
                msg = await call.message.answer(
                    text=text_msg, 
                    parse_mode="HTML",
                    reply_markup=get_client_deal_keyboard(deal_id)
                )
                add_message(global_msg_fast, user_id, msg)
        else:
            msg = await call.message.answer("у вас нет сделок на котрые вы записались как клиент 🥸")
            add_message(global_msg_fast, user_id, msg)
            
        if provider_deals:
            msg = await call.message.answer("список открытых сделок где клиенты записались на ваши услуги 😎")
            add_message(global_msg_fast, user_id, msg)
            for deal in provider_deals:
                c_id = deal.get(DealFields.SERVICE_CLIENT_ID.value)
                c_profile = profiles.get(c_id) or profiles.get(str(c_id)) or {}
                c_name = c_profile.get(UserProfileFields.NAME.value) or f"ID {c_id}"
                
                deal_id = deal.get(DealFields.DEAL_ID.value)
                text_msg = format_deal_msg(deal, c_name, False)
                
                msg = await call.message.answer(
                    text=text_msg, 
                    parse_mode="HTML",
                    reply_markup=get_provider_deal_keyboard(deal_id)
                )
                add_message(global_msg_fast, user_id, msg)
        else:
            msg = await call.message.answer("у вас нет сделок где клиенты записались на ваши услуги 😎")
            add_message(global_msg_fast, user_id, msg)
            
        msg = await call.message.answer(
            "это все активные сделки котрые я нашел по вашему профилю",
            reply_markup=get_inline_keyboard_close()
        )
        add_message(global_msg_fast, user_id, msg)
        return
    elif data == MainMenuButtons.SUPPORT.name.lower():
        await call.answer()
        msg = await call.message.answer(
            f"Для решения любых вопросов вы можете написать нашему модератору {config.MODERATOR_USERNAME}",
            reply_markup=get_inline_keyboard_close()
        )
        add_message(global_msg_fast, user_id, msg)
        return

    # 8. Исполнитель принимает заявку (ACCEPT_REQUEST)
    elif data.startswith(f"{MainMenuButtons.ACCEPT_REQUEST.name.lower()}_"):
        try:
            _, deal_id = data.rsplit('_', 1)
        except ValueError:
            await bot.send_message(chat_id=user_id, text="Ошибка данных")
            await call.answer()
            return

        deals = load_deals_locked()
        deal = deals.get(deal_id)
        if not deal:
            await bot.send_message(chat_id=user_id, text="Сделка не найдена")
            await call.answer()
            return
            
        if deal.get(DealFields.STATUS_DEAL.value) != DealStatus.PENDING_CONFIRMATION.value:
            await bot.send_message(chat_id=user_id, text="Заявка уже обработана")
            await call.answer()
            return

        # Обновляем статус
        deal[DealFields.STATUS_DEAL.value] = DealStatus.IN_PROGRESS.value
        save_deals_locked(deals)
        
        # Редактируем сообщение (убираем клавиатуру, добавляем ✅ принято)
        try:
            original_text = call.message.text
            new_text = f"{original_text}\n\n✅ <b>Принято</b>"
            await call.message.edit_text(new_text, reply_markup=None, parse_mode="HTML")
        except Exception as e:
            print(f"Ошибка редактирования сообщения: {e}")

        # Получаем данные сторон
        client_id = deal.get(DealFields.SERVICE_CLIENT_ID.value)
        provider_id = user_id
        
        users_dict = load_all_users()
        
        client_data = users_dict.get(client_id) or users_dict.get(str(client_id)) or {}
        client_tg = client_data.get(UserFields.NAME_TG.value, f"ID {client_id}")
        if not client_tg.startswith("@") and client_tg != f"ID {client_id}":
            client_tg = f"@{client_tg}"
            
        provider_data = users_dict.get(provider_id) or users_dict.get(str(provider_id)) or {}
        provider_tg = provider_data.get(UserFields.NAME_TG.value, f"ID {provider_id}")
        if not provider_tg.startswith("@") and provider_tg != f"ID {provider_id}":
            provider_tg = f"@{provider_tg}"

        # Отправляем сообщение исполнителю
        try:
            await bot.send_message(
                chat_id=provider_id,
                text=f"Для того чтобы договориться об услуге, напишите {client_tg} или подождите, пока он вам сам напишет."
            )
        except Exception as e:
            print(f"Ошибка отправки контактов исполнителю: {e}")

        # Отправляем сообщение клиенту
        service_name = deal.get(DealFields.SERVICE_NAME.value, "Услуга")
        try:
            await bot.send_message(
                chat_id=client_id,
                text=f"Заявка на услугу <b>{service_name}</b> получена и принята! Для обсуждения деталей свяжитесь с {provider_tg}.",
                parse_mode="HTML"
            )
        except Exception as e:
            print(f"Ошибка отправки контактов клиенту: {e}")

        await bot.send_message(chat_id=user_id, text="Заявка принята!", reply_markup=get_persistent_main_menu())
        await call.answer()
        return

    # 9. Исполнитель отклоняет заявку (REJECT_REQUEST)
    elif data.startswith(f"{MainMenuButtons.REJECT_REQUEST.name.lower()}_"):
        try:
            _, deal_id = data.rsplit('_', 1)
        except ValueError:
            await bot.send_message(chat_id=user_id, text="Ошибка данных")
            await call.answer()
            return

        deals = load_deals_locked()
        deal = deals.get(deal_id)
        if not deal:
            await bot.send_message(chat_id=user_id, text="Сделка не найдена")
            await call.answer()
            return

        if deal.get(DealFields.STATUS_DEAL.value) != DealStatus.PENDING_CONFIRMATION.value:
            await bot.send_message(chat_id=user_id, text="Заявка уже обработана")
            await call.answer()
            return

        # Обновляем статус
        deal[DealFields.STATUS_DEAL.value] = DealStatus.CANCELLED.value
        save_deals_locked(deals)

        # Редактируем сообщение (убираем клавиатуру, добавляем 🛑 отклонили запрос)
        try:
            original_text = call.message.text
            new_text = f"{original_text}\n\n🛑 <b>Отклонили запрос</b>"
            await call.message.edit_text(new_text, reply_markup=None, parse_mode="HTML")
        except Exception as e:
            print(f"Ошибка редактирования сообщения: {e}")

        client_id = deal.get(DealFields.SERVICE_CLIENT_ID.value)
        price_to_refund = float(deal.get(DealFields.PRICE_IN_COINS.value, 0))
        required_amount = round(price_to_refund * 1.1, 2)
        
        # Разблокируем монеты клиенту
        lock = FileLock(f"{config.ALL_USERS_PATH}.lock")
        with lock:
            from services.users_utils.all_users_manager import ALL_USERS_LIST
            users = load_all_users()
            buyer_data = users.get(client_id) or users.get(str(client_id))
            if buyer_data:
                current_block = float(buyer_data.get(UserMetrics.BLOCK_BALANCE.value, 0))
                # Защита от отрицательного баланса блокировки
                new_block = max(0.0, current_block - required_amount)
                buyer_data[UserMetrics.BLOCK_BALANCE.value] = round(new_block, 2)
                ALL_USERS_LIST.clear()
                ALL_USERS_LIST.update(users)
                save_all_users()

        service_name = deal.get(DealFields.SERVICE_NAME.value, "Услуга")
        # Уведомляем клиента об отмене
        try:
            await bot.send_message(
                chat_id=client_id,
                text=f"К сожалению, исполнитель отклонил вашу заявку на услугу <b>{service_name}</b>.\nВаши <b>{required_amount:g}</b> монет разблокированы.",
                parse_mode="HTML"
            )
        except Exception as e:
            print(f"Ошибка отправки уведомления об отмене клиенту: {e}")

        await bot.send_message(chat_id=user_id, text="Заявка отклонена, средства возвращены клиенту.")
        await call.answer()
        return
