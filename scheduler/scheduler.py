# scheduler.py
import asyncio
import logging
from datetime import datetime, timezone, timedelta
from filelock import FileLock

from initApp.config_loader import config
from loggingConfig.colorFormatter import YELLOW, RESET
from entity.Enums_entity import UserFields, UserLifecycleStatus, DealStatus, DealFields, UserMetrics
from services.keyboards.keyboards_for_CONTACTED import get_contacted_keyboard
from services.users_utils.all_users_manager import load_all_users, save_all_users, ALL_USERS_LIST
from services.users_utils.deals_manager import load_deals_locked, save_deals_locked
from services.send_msg_utils.utuls_send_msg import safe_send_message


async def run_registration_reminders(bot):
    """
    Раз в N минут проверяет пользователей со статусом contacted.
    Если с момента регистрации (или обновления) прошёл 1 час и напоминание ещё не отправлено,
    то шлёт напоминание.
    """
    sleep_seconds = getattr(config, "SCHEDULER_INTERVAL_REMINDER_MIN", 15) * 60
    
    while True:
        logging.debug(f"{YELLOW} [SCHEDULER] Проверка анкет на напоминание (contacted)... {RESET}")
        try:
            lock_users = FileLock(f"{config.ALL_USERS_PATH}.lock")
            with lock_users:
                users = load_all_users()
                changed = False
                now = datetime.now(timezone.utc)
                
                for user_id, user_data in users.items():
                    # Исключаем модератора и разработчика из рассылки-напоминания
                    if str(user_id) in [str(getattr(config, "MODERATOR_CONTACT_ID", "")), str(getattr(config, "DEVELOPER_CHAT_ID", ""))]:
                        continue
                    
                    # Проверяем статус contacted
                    if user_data.get(UserFields.STATUS.value) != UserLifecycleStatus.CONTACTED.value:
                        continue
                        
                    # Проверяем, отправляли ли уже пуш
                    if user_data.get(UserFields.REGISTRATION_REMINDER_SENT.value) is True:
                        continue

                    # Вычисляем время
                    date_str = user_data.get(UserFields.UPDATED_AT.value) or user_data.get(UserFields.DATE_REG.value)
                    if not date_str:
                        continue
                        
                    try:
                        record_date = datetime.fromisoformat(date_str).replace(tzinfo=timezone.utc)
                    except ValueError:
                        continue

                    # Если прошел 1 час (60 минут)
                    if now - record_date > timedelta(hours=1):
                        logging.info(f"[SCHEDULER] Отправка напоминания об анкете юзеру {user_id}")
                        text_reminder = (
                            "упс, хотел вас порекоменодовать другим участникам бартерного клуба , "
                            "но вижу что ваша анкета еще не отправдена на проверку  пожалуйста расскажите о себе -заполните анкету"
                        )
                        # Пытаемся отправить
                        try:
                            await safe_send_message(bot, chat_id=int(user_id), text=text_reminder, reply_markup=get_contacted_keyboard())
                            # Если ок, ставим флаг
                            user_data[UserFields.REGISTRATION_REMINDER_SENT.value] = True
                            changed = True
                        except Exception as e:
                            logging.error(f"[SCHEDULER] Ошибка отправки напоминания юзеру {user_id}: {e}")

                if changed:
                    ALL_USERS_LIST.clear()
                    ALL_USERS_LIST.update(users)
                    save_all_users()

        except Exception as e:
            logging.error(f"[SCHEDULER ERROR] В цикле run_registration_reminders: {e}")

        await asyncio.sleep(sleep_seconds)


async def run_auto_cancel_deals(bot):
    """
    Раз в N минут проверяет зависшие сделки (pending_confirmation).
    Если с момента создания сделки прошло 24 часа, она автоматически отменяется.
    Деньги размораживаются со счета block_balance клиента и возвращаются на его основной balance.
    Шлет уведомления модератору, клиенту и исполнителю.
    """
    sleep_seconds = getattr(config, "SCHEDULER_INTERVAL_AUTO_CANCEL_MIN", 60) * 60
    
    while True:
        logging.debug(f"{YELLOW} [SCHEDULER] Проверка зависших сделок (pending_confirmation)... {RESET}")
        try:
            deals = load_deals_locked()
            deals_changed = False
            now = datetime.now(timezone.utc)
            
            # Собираем ID зависших сделок
            deals_to_cancel = []
            
            for deal_id, deal in deals.items():
                if deal.get(DealFields.STATUS_DEAL.value) != DealStatus.PENDING_CONFIRMATION.value:
                    continue
                    
                date_str = deal.get(DealFields.CREATED_AT.value) or deal.get(DealFields.UPDATED_AT.value)
                if not date_str:
                    continue
                    
                try:
                    record_date = datetime.fromisoformat(date_str).replace(tzinfo=timezone.utc)
                except ValueError:
                    continue

                # 24 часа
                if now - record_date > timedelta(hours=24):
                    deals_to_cancel.append(deal_id)

            if deals_to_cancel:
                # Работаем с балансами, поэтому лочим юзеров
                lock_users = FileLock(f"{config.ALL_USERS_PATH}.lock")
                with lock_users:
                    users = load_all_users()
                    users_changed = False
                    
                    for deal_id in deals_to_cancel:
                        deal = deals[deal_id]
                        client_id = str(deal.get(DealFields.SERVICE_CLIENT_ID.value))
                        provider_id = str(deal.get(DealFields.SERVICE_PROVIDER_ID.value))
                        price = float(deal.get(DealFields.PRICE_IN_COINS.value, 0))
                        
                        logging.info(f"[SCHEDULER] Авто-отмена сделки {deal_id}. Разморозка {price} коинов клиенту {client_id}")
                        
                        client_data = users.get(client_id)
                        if client_data:
                            # Возвращаем заблокированные средства на баланс
                            block_bal = float(client_data.get(UserMetrics.BLOCK_BALANCE.value, 0))
                            normal_bal = float(client_data.get(UserMetrics.BALANCE.value, 0))
                            
                            # Защита от отрицательного баланса (на всякий случай)
                            unblock_amount = min(price, block_bal) if block_bal > 0 else price
                            
                            client_data[UserMetrics.BLOCK_BALANCE.value] = round(max(0.0, block_bal - unblock_amount), 2)
                            client_data[UserMetrics.BALANCE.value] = round(normal_bal + price, 2)
                            users_changed = True

                        deal[DealFields.STATUS_DEAL.value] = DealStatus.CANCELLED.value
                        deal[DealFields.DATA_CANCELLED_AT.value] = now.isoformat()
                        deals_changed = True

                        # Рассылка алёртов
                        reason = "Истекло время подтверждения (24ч). Исполнитель не ответил на заявку."
                        
                        text_client = f"⚠️ Ваша сделка `{deal_id}` автоматически отменена.\nПричина: {reason}\nВаши {price} 🪙 разблокированы."
                        text_provider = f"⚠️ Ваша потенциальная сделка `{deal_id}` отменена из-за отсутствия ответа более суток."
                        text_mod = f"🛑 Авто-отмена сделки `{deal_id}`.\nКлиент: {client_id}\nИсполнитель: {provider_id}\nПричина: {reason}"
                        
                        if client_id:
                            await safe_send_message(bot, chat_id=client_id, text=text_client, parse_mode="Markdown")
                        if provider_id:
                            await safe_send_message(bot, chat_id=provider_id, text=text_provider, parse_mode="Markdown")
                        
                        await safe_send_message(bot, chat_id=config.MODERATOR_CONTACT_ID, text=text_mod, parse_mode="Markdown")

                    if users_changed:
                        ALL_USERS_LIST.clear()
                        ALL_USERS_LIST.update(users)
                        save_all_users()

            if deals_changed:
                save_deals_locked(deals)

        except Exception as e:
            logging.error(f"[SCHEDULER ERROR] В цикле run_auto_cancel_deals: {e}")

        await asyncio.sleep(sleep_seconds)
