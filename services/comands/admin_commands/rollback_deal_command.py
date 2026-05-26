from aiogram import Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from filelock import FileLock

from entity.Enums_entity import UserFields, UserMetrics, DealStatus, DealFields
from initApp.config_loader import config
from services.users_utils.all_users_manager import load_all_users, save_all_users, ALL_USERS_LIST
from services.users_utils.deals_manager import load_deals_locked, save_deals_locked
from services.users_utils.reviews_manager import load_reviews_locked, save_reviews_locked
from services.keyboards.bot_all_buttons import ModeratorChatButtons
from services.keyboards.creator_persistent_keyboards import get_cancel_keyboard, get_persistent_moderator_menu
from services.state_bot.global_store import add_message, global_msg_fast
from handlers.fsm_utils import set_waiting_input, check_cancel_input, clear_waiting_input
from services.msgs_utils.deleter_messages import clear_messages
from services.send_msg_utils.utuls_send_msg import safe_send_message


async def start_rollback_deal_input(call: CallbackQuery, bot: Bot, state: FSMContext):
    """
    Start process of rolling back a deal.
    Sets FSM state to wait for input: "deal_id".
    """
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    
    await set_waiting_input(
        state, bot, chat_id, user_id,
        command_name=ModeratorChatButtons.ROLLBACK_DEAL.name.lower(),
        timeout=config.TIME_TO_INPUT_MSG_FSM
    )
    
    msg = await call.message.answer(
        text="Введи ID сделки для отката (вернём деньги клиенту, удалим отзыв).\nПример: `17909872531771846780`",
        parse_mode="Markdown",
        reply_markup=get_cancel_keyboard()
    )
    add_message(global_msg_fast, user_id, msg)
    await call.answer()


async def process_rollback_deal_input(message: Message, state: FSMContext, bot: Bot):
    """
    Process the input for rolling back a deal.
    Expected format: "deal_id"
    """
    user_id = message.from_user.id
    chat_id = message.chat.id

    # Check for cancel
    if await check_cancel_input(message.text, message, state):
        await clear_messages(user_id, global_msg_fast)
        return

    text = message.text.strip()
    deal_id = text

    if not deal_id:
        msg = await message.answer("⚠️ Неверный формат. Введи числовой ID сделки.")
        add_message(global_msg_fast, user_id, msg)
        add_message(global_msg_fast, user_id, message)
        return

    # Загружаем сделки
    deals = load_deals_locked()
    deal = deals.get(deal_id)
    if not deal:
        msg = await message.answer(f"❌ Сделка {deal_id} не найдена в базе данных.")
        add_message(global_msg_fast, user_id, msg)
        add_message(global_msg_fast, user_id, message)
        return

    status = deal.get(DealFields.STATUS_DEAL.value)
    if status == DealStatus.CANCELLED.value:
        msg = await message.answer(f"⚠️ Сделка {deal_id} уже имеет статус ОТМЕНЕНА.")
        add_message(global_msg_fast, user_id, msg)
        add_message(global_msg_fast, user_id, message)
        return

    client_id = deal.get(DealFields.SERVICE_CLIENT_ID.value)
    provider_id = deal.get(DealFields.SERVICE_PROVIDER_ID.value)
    price_in_coins = float(deal.get(DealFields.PRICE_IN_COINS.value, 0))
    
    # Расчеты сделки:
    total_cost = round(price_in_coins * 1.1, 2)
    provider_earnings = round(price_in_coins, 2)
    server_commission = round(price_in_coins * 0.1, 2)

    is_finished = (status == DealStatus.FINISHED.value)

    lock = FileLock(f"{config.ALL_USERS_PATH}.lock")
    with lock:
        users = load_all_users()
        
        provider_data = users.get(provider_id) or users.get(str(provider_id))
        client_data = users.get(client_id) or users.get(str(client_id))
        mod_data = users.get(config.MODERATOR_CONTACT_ID) or users.get(str(config.MODERATOR_CONTACT_ID))

        if not provider_data or not client_data:
            msg = await message.answer("❌ Ошибка: клиент или исполнитель не найден в базе пользователей `all_users.json`.")
            add_message(global_msg_fast, user_id, msg)
            add_message(global_msg_fast, user_id, message)
            return

        mod_warning = ""

        if is_finished:
            provider_balance = float(provider_data.get(UserMetrics.BALANCE.value, 0))
            
            # Проверяем, хватает ли у провайдера монет на возврат
            if provider_balance < provider_earnings:
                msg = await message.answer(
                    f"❌ Откат невозможен — исполнитель (ID: {provider_id}) уже потратил полученные монеты. Баланса для возврата недостаточно.\n"
                    f"Его баланс: {provider_balance}, нужно для возврата {provider_earnings}."
                )
                add_message(global_msg_fast, user_id, msg)
                add_message(global_msg_fast, user_id, message)
                return

            # 1. Снимаем у исполнителя
            provider_data[UserMetrics.BALANCE.value] = round(provider_balance - provider_earnings, 2)
            
            # 2. Возвращаем клиенту полную сумму (с учетом комиссии)
            client_balance = float(client_data.get(UserMetrics.BALANCE.value, 0))
            client_data[UserMetrics.BALANCE.value] = round(client_balance + total_cost, 2)
            
            # 3. Списываем комиссию у модератора
            if mod_data:
                mod_balance = float(mod_data.get(UserMetrics.BALANCE.value, 0))
                new_mod_balance = round(mod_balance - server_commission, 2)
                mod_data[UserMetrics.BALANCE.value] = new_mod_balance
                if new_mod_balance < 0:
                    mod_warning = f"\n⚠️ **Внимание!** Баланс аккаунта модератора (ID: {config.MODERATOR_CONTACT_ID}) ушел в минус: {new_mod_balance} 🪙"
        else:
            # Сделка еще в процессе (in_progress или pending_confirmation)
            # 1. У исполнителя ничего не списываем (он ничего не получал)
            # 2. Размораживаем монеты клиенту в block_balance (реальный баланс не менялся)
            client_block = float(client_data.get(UserMetrics.BLOCK_BALANCE.value, 0))
            new_block = max(0.0, client_block - total_cost)
            client_data[UserMetrics.BLOCK_BALANCE.value] = round(new_block, 2)

            # 3. У модератора комиссия еще не списывалась, так что ничего не меняем

        ALL_USERS_LIST.clear()
        ALL_USERS_LIST.update(users)
        save_all_users()

    # Меняем статус сделки
    deal[DealFields.STATUS_DEAL.value] = DealStatus.CANCELLED.value
    save_deals_locked(deals)

    # Удаляем отзыв, относящийся к сделке (из reviews.json)
    reviews_db = load_reviews_locked()
    keys_to_delete = []
    for r_id, r_data in reviews_db.items():
        if r_data.get("deal_id") == str(deal_id):
            keys_to_delete.append(r_id)
            
    for k in keys_to_delete:
        del reviews_db[k]
        
    if keys_to_delete:
        save_reviews_locked(reviews_db)

    # Уведомляем
    if is_finished:
        msg_text = (
            f"✅ Сделка `{deal_id}` успешно отменена (ОТКАТ ЗАВЕРШЕННОЙ СДЕЛКИ).\n"
            "Деньги списаны с исполнителя и возвращены клиенту на основной баланс, отзыв удалён.\n"
            f"- Заказчику возвращено на баланс: {total_cost} 🪙\n"
            f"- У исполнителя списано с баланса: {provider_earnings} 🪙\n"
            f"- Списана комиссия модератора: {server_commission} 🪙\n"
            f"- Удалено отзывов: {len(keys_to_delete)}"
            f"{mod_warning}"
        )
    else:
        msg_text = (
            f"✅ Активная сделка `{deal_id}` успешно отменена модератором.\n"
            f"Заблокированные монеты клиента разморожены в block_balance.\n"
            f"- Заказчику разблокировано: {total_cost} 🪙 в block_balance\n"
            f"- Исполнитель и модератор не задействованы (сделка не была завершена)."
        )

    success_msg = await message.answer(
        text=msg_text,
        parse_mode="Markdown", reply_markup=get_persistent_moderator_menu()
    )
    # Очищаем форму FSM
    await clear_waiting_input(state, chat_id, user_id)
