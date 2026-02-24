from aiogram import Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from filelock import FileLock
import html

from entity.Enums_entity import DealStatus, DealFields, UserFields, UserMetrics, UserProfileFields
from services.keyboards.bot_all_buttons import DealProcessButtons, CommandsBot, MainMenuButtons
from services.msgs_utils.deleter_messages import clear_messages
from services.state_bot.global_store import add_message, global_msg_fast
from services.users_utils.deals_manager import load_deals_locked, save_deals_locked
from services.users_utils.user_profile_manager import load_profiles
from services.users_utils.all_users_manager import ALL_USERS_LIST, load_all_users, save_all_users
from initApp.config_loader import config
from services.state_bot.global_store import remove_message_from_all_storages
from services.send_msg_utils.utuls_send_msg import safe_send_message

async def handle_deal_process_callbacks(call: CallbackQuery, bot: Bot, state: FSMContext):
    """
    Обработчик кнопок процесса сделки (отмена, завершение).
    """
    data = call.data
    user_id = call.from_user.id
    
    # 0. Защита: спасаем текущее сообщение с кнопками от массового удаления!
    if call.message:
        remove_message_from_all_storages(call.message.message_id)
        
    await clear_messages(user_id, global_msg_fast)
    
    if data.startswith(f"{DealProcessButtons.CANCEL_DEAL.name.lower()}_"):
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

        status = deal.get(DealFields.STATUS_DEAL.value)
        client_id = deal.get(DealFields.SERVICE_CLIENT_ID.value)
        provider_id = deal.get(DealFields.SERVICE_PROVIDER_ID.value)
        service_name = html.escape(str(deal.get(DealFields.SERVICE_NAME.value, "Услуга")))
        
        profiles = load_profiles()
        users = load_all_users()
        
        client_name = profiles.get(client_id, {}).get(UserProfileFields.NAME.value) or f"ID {client_id}"
        provider_name = users.get(provider_id, {}).get(UserFields.NAME_TG.value) or f"ID {provider_id}"
        if provider_name != f"ID {provider_id}" and not provider_name.startswith("@"):
            provider_name = f"@{provider_name}"
        
        client_name = html.escape(str(client_name))
        provider_name = html.escape(str(provider_name))

        if status == DealStatus.CANCELLED.value:
            await bot.send_message(chat_id=user_id, text="Сделка уже отменена")
            await call.answer()
            return

        # --- 1. ЕСЛИ НАЖИМАЕТ КЛИЕНТ (service_client_id) ---
        if user_id == client_id:
            # 1-1. Услуга в статусе pending_confirmation
            if status == DealStatus.PENDING_CONFIRMATION.value:
                # Отменяем, размораживаем баланс клиенту
                deal[DealFields.STATUS_DEAL.value] = DealStatus.CANCELLED.value
                save_deals_locked(deals)
                
                price_to_refund = float(deal.get(DealFields.PRICE_IN_COINS.value, 0))
                required_amount = round(price_to_refund * 1.1, 2)
                
                lock = FileLock(f"{config.ALL_USERS_PATH}.lock")
                with lock:
                    users = load_all_users()
                    buyer_data = users.get(client_id) or users.get(str(client_id))
                    if buyer_data:
                        current_block = float(buyer_data.get(UserMetrics.BLOCK_BALANCE.value, 0))
                        new_block = max(0.0, current_block - required_amount)
                        buyer_data[UserMetrics.BLOCK_BALANCE.value] = round(new_block, 2)
                        ALL_USERS_LIST.clear()
                        ALL_USERS_LIST.update(users)
                        save_all_users()

                try:
                    original_text = call.message.text
                    new_text = f"{original_text}\n\n🛑 <b>Отменено</b>"
                    await call.message.edit_text(new_text, reply_markup=None, parse_mode="HTML")
                except Exception:
                    pass

                cancel_msg = f"Клиент <b>{client_name}</b> отменил запись на услугу <b>{service_name}</b> (ID: <code>{deal_id}</code>)."
                try:
                    await bot.send_message(chat_id=client_id, text=cancel_msg, parse_mode="HTML")
                except Exception:
                    pass
                try:
                    await bot.send_message(chat_id=provider_id, text=cancel_msg, parse_mode="HTML")
                except Exception:
                    pass
                return

            # 1-2. Услуга в статусе in_progress
            elif status == DealStatus.IN_PROGRESS.value:
                provider_msg = (
                    f"Клиент <b>{client_name}</b> (Сделка: <code>{deal_id}</code>, Услуга: <b>{service_name}</b>) "
                    f"хочет отменить сделку.\n\n"
                    f"Вы можете сделать это в меню:\n"
                    f"👉 {CommandsBot.MENU.value} -> {MainMenuButtons.CONFIRM_DEAL.value} -> найдите сделку и отмените запись.\n\n"
                    f"Отмените, если клиент не нарушил правила сделки, услуга не была оказана, и отмена произошла заблаговременно.\n\n"
                    f"В спорных ситуациях пишите модератору {config.MODERATOR_USERNAME}."
                )
                try:
                    await bot.send_message(chat_id=provider_id, text=provider_msg, parse_mode="HTML")
                except Exception:
                    pass

                client_msg = (
                    f"Пожалуйста, напишите исполнителю <b>{provider_name}</b> и попросите отменить через меню сделок.\n\n"
                    f"Учтите, что для отмены необходимо, чтобы с вашей стороны не было нарушения правил сделки, "
                    f"услуга не была оказана, и отмена происходит заблаговременно.\n\n"
                    f"В спорных ситуациях пишите модератору {config.MODERATOR_USERNAME}."
                )
                try:
                    from services.keyboards.sustem_inline_keyboard import get_inline_keyboard_close
                    msg = await call.message.answer(text=client_msg, parse_mode="HTML", reply_markup=get_inline_keyboard_close())
                    add_message(global_msg_fast, user_id, msg)
                except Exception:
                    pass
                # await call.answer()
                return

        # --- 2. ЕСЛИ НАЖИМАЕТ ИСПОЛНИТЕЛЬ (service_provider_id) ---
        elif user_id == provider_id:
            # Исполнитель завершает (отменяет) сделку в любой момент
            deal[DealFields.STATUS_DEAL.value] = DealStatus.CANCELLED.value
            save_deals_locked(deals)
            
            price_to_refund = float(deal.get(DealFields.PRICE_IN_COINS.value, 0))
            required_amount = round(price_to_refund * 1.1, 2)
            
            lock = FileLock(f"{config.ALL_USERS_PATH}.lock")
            with lock:
                users = load_all_users()
                buyer_data = users.get(client_id) or users.get(str(client_id))
                if buyer_data:
                    current_block = float(buyer_data.get(UserMetrics.BLOCK_BALANCE.value, 0))
                    new_block = max(0.0, current_block - required_amount)
                    buyer_data[UserMetrics.BLOCK_BALANCE.value] = round(new_block, 2)
                    ALL_USERS_LIST.clear()
                    ALL_USERS_LIST.update(users)
                    save_all_users()

            try:
                original_text = call.message.text
                new_text = f"{original_text}\n\n🛑 <b>Отменено</b>"
                await call.message.edit_text(new_text, reply_markup=None, parse_mode="HTML")
            except Exception:
                pass

            cancel_msg = f"Исполнитель <b>{provider_name}</b> отменил запись на услугу <b>{service_name}</b> (ID: <code>{deal_id}</code>)."
            try:
                await bot.send_message(chat_id=client_id, text=cancel_msg, parse_mode="HTML")
            except Exception:
                pass
            try:
                await bot.send_message(chat_id=provider_id, text=cancel_msg, parse_mode="HTML")
            except Exception:
                pass
            return
            
        else:
            await bot.send_message(chat_id=user_id, text="Вы не являетесь участником этой сделки.")
            await call.answer()
            return

    elif data.startswith(f"{DealProcessButtons.SERVICE_DONE.name.lower()}_"):
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

        status = deal.get(DealFields.STATUS_DEAL.value)
        
        if status == DealStatus.PENDING_CONFIRMATION.value:
            msg = await bot.send_message(chat_id=user_id, text="Нельзя подтвердить услугу\n\nПричина: Представитель услуги еще не принял ваш запрос на услугу.")
            add_message(global_msg_fast, user_id, msg)
            await call.answer()
            return
            
        if status != DealStatus.IN_PROGRESS.value:
            await bot.send_message(chat_id=user_id, text=f"Сделка уже в статусе: {status}")
            await call.answer()
            return

        client_id = deal.get(DealFields.SERVICE_CLIENT_ID.value)
        if str(user_id) != str(client_id):
            await bot.send_message(chat_id=user_id, text="Только заказчик может подтвердить выполнение услуги.")
            await call.answer()
            return

        provider_id = deal.get(DealFields.SERVICE_PROVIDER_ID.value)
        service_name = html.escape(str(deal.get(DealFields.SERVICE_NAME.value, "Услуга")))
        price_in_coins = float(deal.get(DealFields.PRICE_IN_COINS.value, 0))
        
        # Экономика:
        total_cost = round(price_in_coins * 1.1, 2)
        provider_earnings = round(price_in_coins, 2)
        server_commission = round(price_in_coins * 0.1, 2)

        # Обновляем структуру сделки
        deal[DealFields.STATUS_DEAL.value] = DealStatus.FINISHED.value
        deal[DealFields.REVIEW_ALREADY_LEFT.value] = False
        save_deals_locked(deals)

        # Проводим балансовые операции
        lock = FileLock(f"{config.ALL_USERS_PATH}.lock")
        with lock:
            users = load_all_users()
            
            # 1. Списываем у клиента
            buyer_data = users.get(client_id) or users.get(str(client_id))
            if buyer_data:
                current_block = float(buyer_data.get(UserMetrics.BLOCK_BALANCE.value, 0))
                current_balance = float(buyer_data.get(UserMetrics.BALANCE.value, 0))
                buyer_data[UserMetrics.BLOCK_BALANCE.value] = round(max(0.0, current_block - total_cost), 2)
                buyer_data[UserMetrics.BALANCE.value] = round(max(0.0, current_balance - total_cost), 2)
                
            # 2. Зачисляем исполнителю
            seller_data = users.get(provider_id) or users.get(str(provider_id))
            if seller_data:
                current_balance = float(seller_data.get(UserMetrics.BALANCE.value, 0))
                seller_data[UserMetrics.BALANCE.value] = round(current_balance + provider_earnings, 2)
                
            # 3. Зачисляем комиссию модератору
            mod_data = users.get(config.MODERATOR_CONTACT_ID) or users.get(str(config.MODERATOR_CONTACT_ID))
            if mod_data:
                current_mod_balance = float(mod_data.get(UserMetrics.BALANCE.value, 0))
                mod_data[UserMetrics.BALANCE.value] = round(current_mod_balance + server_commission, 2)
                
            ALL_USERS_LIST.clear()
            ALL_USERS_LIST.update(users)
            save_all_users()

        from services.keyboards.creator_inline_keyboards import get_leave_review_keyboard
        
        profiles = load_profiles()
        users = load_all_users()
        
        client_name = profiles.get(client_id, {}).get(UserProfileFields.NAME.value) or f"ID {client_id}"
        provider_name = users.get(provider_id, {}).get(UserFields.NAME_TG.value) or f"ID {provider_id}"
        if provider_name != f"ID {provider_id}" and not provider_name.startswith("@"):
            provider_name = f"@{provider_name}"
            
        client_name = html.escape(str(client_name))
        provider_name = html.escape(str(provider_name))

        # Уведомления
        provider_msg = f"Вы оказали услугу <b>{service_name}</b> - ваш баланс пополнен на <b>{provider_earnings:g}</b> 🪙"
        client_msg = f"Вы получили услугу <b>{service_name}</b> - ваш баланс уменьшен на <b>{total_cost:g}</b> 🪙\n(цена услуги: {provider_earnings:g}, сервисный сбор: {server_commission:g}) \n\n <b>Плиз, оставьте звезды рейтинга и отзыв исполнителю</b>"
        mod_msg = f"Произошла сделка между клиентом <b>{client_name}</b> и исполнителем <b>{provider_name}</b> на услугу <b>{service_name}</b> (Сделка: <code>{deal_id}</code>).\nВаша комиссия составила <b>{server_commission:g}</b> 🪙."

        await safe_send_message(bot, chat_id=user_id, text="Сделка успешно завершена!")
        await safe_send_message(bot, chat_id=provider_id, text=provider_msg, parse_mode="HTML")
        await safe_send_message(bot, chat_id=client_id, text=client_msg, parse_mode="HTML", reply_markup=get_leave_review_keyboard(deal_id))
        await safe_send_message(bot, chat_id=config.MODERATOR_CONTACT_ID, text=mod_msg, parse_mode="HTML")

        # add_message(global_msg_fast, user_id, msg)
        try:
            original_text = call.message.text
            new_text = f"{original_text}\n\n✅ <b>Услуга подтверждена - монеты отправлены </b>"
            await call.message.edit_text(new_text, reply_markup=None, parse_mode="HTML")
        except Exception:
            pass

        await call.answer()
        return
