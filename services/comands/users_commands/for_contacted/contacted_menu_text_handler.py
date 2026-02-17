from aiogram import Bot
from aiogram.types import Message

from entity.Enums_entity import UserFlags
from services.keyboards.bot_all_buttons import CONTACTED_Menu
from services.keyboards.keyboards_for_CONTACTED import get_agree_keyboard, get_contacted_keyboard, get_anketa_keyboard
from services.users_utils.all_users_manager import load_all_users, save_all_users
from services.state_bot.global_store import add_message, global_msg_contacted_fast
from services.msgs_utils.deleter_messages import clear_messages
from services.keyboards.keyboards_for_registration import get_accept_rules_keyboard, get_full_name_keyboard

async def handle_contacted_menu_text_commands(message: Message, bot: Bot):
    """
    Обработчик команд из меню CONTACTED_Menu.
    """
    text = (message.text or "").casefold()
    user_id = message.from_user.id

    # 1. Подать заявку на вступление
    if text == CONTACTED_Menu.APPLY_REQUEST.value.casefold():
        add_message(global_msg_contacted_fast, user_id, message)
        await clear_messages(user_id, global_msg_contacted_fast)
        
        rules_text = (
            "📜 **Правила клуба:**\n\n"
            "1. Уважайте других участников.\n"
            "2. Выполняйте обязательства по сделкам.\n"
            "3. Честно описывайте свои услуги.\n\n"
            "Пожалуйста, прочитайте и примите правила, чтобы продолжить."
        )
        msg = await bot.send_message(
            chat_id=user_id,
            text=rules_text,
            reply_markup=get_agree_keyboard()
        )
        add_message(global_msg_contacted_fast, user_id, msg)
        return

    # 1.1 Принять правила клуба
    elif text == CONTACTED_Menu.ACCEPT_RULES.value.casefold():
        add_message(global_msg_contacted_fast, user_id, message)
        await clear_messages(user_id, global_msg_contacted_fast)

        rules_text = (
            "📜 **Правила клуба:**\n\n"
            "1. Уважайте других участников.\n"
            "2. Выполняйте обязательства по сделкам.\n"
            "3. Честно описывайте свои услуги.\n\n"
            "Пожалуйста, прочитайте и примите правила, чтобы продолжить."
        )
        msg = await bot.send_message(
            chat_id=user_id,
            text=rules_text,
            reply_markup=get_agree_keyboard()
        )
        add_message(global_msg_contacted_fast, user_id, msg)
        return

    # 2. Ок-согласен
    elif text == CONTACTED_Menu.OK_AGREE.value.casefold():
        add_message(global_msg_contacted_fast, user_id, message)
        await clear_messages(user_id, global_msg_contacted_fast)

        # Обновляем поле rules_read
        users = load_all_users()
        if user_id in users:
            users[user_id][UserFlags.RULES_READ.value] = True
            save_all_users()

        msg = await bot.send_message(
            chat_id=user_id,
            text="Отлично - вы приняли правила клуба ✅",
            reply_markup=get_anketa_keyboard() # Возвращаем меню, где есть "Заполнить анкету"
        )
        add_message(global_msg_contacted_fast, user_id, msg)
        return
    
    # 3. Заполнить анкету участника
    elif text == CONTACTED_Menu.FILL_PROFILE.value.casefold():
        add_message(global_msg_contacted_fast, user_id, message)
        await clear_messages(user_id, global_msg_contacted_fast)

        from services.users_utils.user_profile_manager import is_profile_completed
        from services.keyboards.keyboards_for_registration import get_final_profile_keyboard

        if is_profile_completed(user_id):
             msg = await bot.send_message(
                chat_id=user_id,
                text="✅ Ваша анкета уже готова!",
                reply_markup=get_final_profile_keyboard()
            )
             add_message(global_msg_contacted_fast, user_id, msg)
             return

        users = load_all_users()
        user_data = users.get(user_id, {})
        rules_read = user_data.get(UserFlags.RULES_READ.value, False)

        if rules_read:
            msg = await bot.send_message(
                chat_id=user_id,
                text="Отлично , расскажите о себе , я спрошу вас обо всем по шагам - для начала давайте заполним ФИО - нажмите на кнопку чтобы внести данные",
                reply_markup=get_full_name_keyboard()
            )
        else:
            msg = await bot.send_message(
                chat_id=user_id,
                text="Вы еще не приняли правила клуба ❌",
                reply_markup=get_accept_rules_keyboard()
            )
        add_message(global_msg_contacted_fast, user_id, msg)
        return

    # 4. Заглушка для остальных
    else:
        # Для заглушки тоже можно делать очистку или просто удалять сообщение пользователя
        # По логике "суть задачи в том чтобы сообщения в чате не копились" - делаем очистку
        add_message(global_msg_contacted_fast, user_id, message)
        await clear_messages(user_id, global_msg_contacted_fast)

        msg = await bot.send_message(
            chat_id=user_id,
            text=f"Заглушка на метод {message.text}"
        )
        add_message(global_msg_contacted_fast, user_id, msg)


