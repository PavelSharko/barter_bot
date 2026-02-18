from handlers.fsm_utils import set_waiting_input
from initApp.config_loader import config
from services.keyboards.bot_all_buttons import AdminChatButtons, ProfileRegistration_Menu, ModeratorChatButtons
from services.keyboards.creator_inline_keyboards import get_moderator_menu_keyboard
from services.keyboards.sustem_inline_keyboard import get_inline_keyboard_close
from services.keyboards.creator_persistent_keyboards import get_cancel_keyboard
from services.msgs_utils.deleter_messages import clear_messages
from services.state_bot.global_store import global_msg_fast, add_message, global_msg_for_close
from services.comands.admin_commands.exclude_participant import start_exclude_participant_input


async def some_method_msg_from_admin_chat(message):
    # todo
    await message.answer("Заглушка метод - если прилетает в группу организаторов бота  текстовое сообщение")
    return

async def some_method_text_msg_from_modertor(message):
    """
    Обрабатывает входящее сообщение от администратора.
    """
    user_id = message.from_user.id
    add_message(global_msg_fast, user_id, message)
    await clear_messages(user_id, global_msg_fast)

    # 1. Если нажата кнопка меню
    if message.text == ModeratorChatButtons.MENU.value:
        # отправляем inline клавиатуру для модератора
        await clear_messages(user_id, global_msg_fast)
        msg = await message.answer(
            text=f"Меню управления модератора 👮‍♂️",
            reply_markup=get_moderator_menu_keyboard()
        )
        add_message(global_msg_fast, user_id, msg)
        return

    else:
        # 2. Любой другой текст (заглушка)
        msg = await message.answer(
            text="я пока не умею понимать текст - воспользуйся меню и кнопками",
            reply_markup=get_moderator_menu_keyboard()
        )
        add_message(global_msg_fast, user_id, msg)
        return



async def handle_callback_from_admin_bot(call, state, bot):
    """
    Обрабатывает callback-запросы, полученные из приватного чата админа с ботом (не из группы).

    Логика:
    - Подтверждает получение callback без всплывающих уведомлений.
    - Очищает глобальные быстрые сообщения пользователя.
    - Обрабатывает конкретные callback-значения, соответствующие кнопкам в меню администратора:
      - Для кнопок BUTTON1 и BUTTON2 отправляет заглушки-ответы.
      - Для кнопки BUTTON_FOR_INSERT_ANYTHING переводит бот в состояние ожидания ввода текста/файлов,
        задаёт таймаут ожидания по конфигу, показывает сообщение с клавиатурой отмены,
        и сохраняет сообщение в глобальное быстрое хранилище.
      - Запоминает команду, чтобы потом в другом месте (FSM) обработать введённые данные.
    """
    await call.answer(text="Принято ✅", show_alert=False)
    user_id = call.from_user.id
    await clear_messages(user_id, global_msg_fast)


    chat_id = call.message.chat.id
    user_id = call.message.from_user.id


    # Обработка действий модератора из меню
    if call.data == ModeratorChatButtons.VIEW_NEW_APPLICATIONS.name.lower():
        msg = await call.message.answer(
            text="вот @ссылка на папку  в гугл диске  базой всех клиентов»\n\nhttps://drive.google.com/drive/folders/1Un16Y5wQy-RWupl0t5n--XZ9KSG80iLu?usp=sharing",
            reply_markup=get_inline_keyboard_close()
        )
        add_message(global_msg_for_close, user_id, msg)
        return

    if call.data == ModeratorChatButtons.EXCLUDE_PARTICIPANT.name.lower():
        from services.comands.admin_commands.exclude_participant import start_exclude_participant_input
        await start_exclude_participant_input(call, bot, state)
        return

    if call.data == ModeratorChatButtons.SEND_COINS.name.lower():
        from services.comands.admin_commands.send_coins import start_send_coins_input
        await start_send_coins_input(call, bot, state)
        return

    if call.data == ModeratorChatButtons.SHOW_BALANCE.name.lower():
        from services.comands.users_commands.show_balance import show_user_balance
        await show_user_balance(call, bot)
        return

    # Обработка действий модератора (Принять/Отклонить)
    if call.data.startswith(f"{ProfileRegistration_Menu.ACCEPT.name.lower()}_") or \
       call.data.startswith(f"{ProfileRegistration_Menu.REJECT.name.lower()}_"):
        from services.comands.admin_commands.moderator_actions import handle_moderator_action
        await handle_moderator_action(call, bot, state)
        return

    # Обработка выбора категории
    if call.data.startswith("category_"):
        from services.comands.admin_commands.moderator_actions import handle_category_selection
        await handle_category_selection(call, bot)
        return



