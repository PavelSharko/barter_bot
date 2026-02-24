from services.msgs_utils.deleter_messages import clear_messages


async def check_and_enforce_unreviewed_deals(user_id: int, bot, call_or_msg, is_callback=False, current_data="") -> bool:
    """Возвращает True, если запрос перехвачен (есть неоставленный отзыв)."""
    from services.users_utils.deals_manager import has_unreviewed_finished_deals
    from services.users_utils.all_users_manager import load_all_users
    from entity.Enums_entity import UserFields, UserLifecycleStatus
    from services.keyboards.creator_inline_keyboards import get_leave_review_keyboard
    from services.state_bot.global_store import add_message, global_msg_fast
    
    users_db = load_all_users()
    user_data = users_db.get(user_id) or users_db.get(str(user_id)) or {}
    
    if user_data.get(UserFields.STATUS.value) != UserLifecycleStatus.CLIENT.value:
        return False
        
    deal_result = has_unreviewed_finished_deals(user_id)
    if not deal_result:
        return False
        
    deal_id, service_name = deal_result

    if is_callback:
        from services.keyboards.bot_all_buttons import ReviewProcessButtons, DealProcessButtons, CommandsBot
        if current_data == CommandsBot.CLOSE.value.lower():
            return False
        allowed_prefixes = [f"{btn.name.lower()}_" for btn in ReviewProcessButtons] + [
            f"{DealProcessButtons.LEAVE_REVIEW.name.lower()}_",
            f"{DealProcessButtons.LEAVE_REVIEW_CLIENT.name.lower()}_"
        ]
        if any(current_data.startswith(prefix) for prefix in allowed_prefixes):
            return False
    else:
        from services.keyboards.bot_all_buttons import ReviewProcessButtons
        if current_data == ReviewProcessButtons.ADD_TEXT_REVIEW.name.lower():
            return False

    text = f"⚠️ Вы еще не оставили отзыв на завершенную сделку по услуге: **{service_name}**.\n\nЧтобы продолжить работу с ботом, пожалуйста, оцените её:"
    await clear_messages(user_id, global_msg_fast)
    
    if is_callback:
        await call_or_msg.answer()
        msg = await bot.send_message(chat_id=user_id, text=text, reply_markup=get_leave_review_keyboard(deal_id))
    else:
        msg = await call_or_msg.answer(text=text, reply_markup=get_leave_review_keyboard(deal_id))
        
    add_message(global_msg_fast, user_id, msg)
    if not is_callback:
        add_message(global_msg_fast, user_id, call_or_msg)
    
    return True
