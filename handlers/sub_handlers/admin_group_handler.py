from handlers.fsm_utils import set_waiting_input
from initApp.config_loader import config
from services.keyboards.bot_all_buttons import AdminChatButtons
from services.keyboards.creator_inline_keyboards import get_menu_keyboard_for_admin_chat
from services.keyboards.creator_persistent_keyboards import get_persistent_main_menu, get_cancel_keyboard
from services.msgs_utils.deleter_messages import clear_messages
from services.state_bot.global_store import global_msg_fast, add_message


async def some_method_msg_from_group_admin(message):
    # todo
    await message.answer("Заглушка метод - если прилетает в чат админа текстовое сообщение")
    return

async def some_method_msg_from_admin(message):
    """
    Обрабатывает входящее сообщение от администратора.

    - Очищает все ранее сохранённые сообщения пользователя из быстрого глобального хранилища.
    - Отправляет основное меню (reply-клавиатуру) для работы админа.
    - Отправляет inline клавиатуру с меню управления для администратора.
    - Сохраняет отправленные и исходные сообщения в глобальное хранилище для последующего управления (например, удаления).
    """
    user_id = message.from_user.id
    await clear_messages(user_id, global_msg_fast)
    # отправляем reply кнопку для админа
    await message.answer(
        text=f"🤖 ",
        reply_markup=get_persistent_main_menu()
    )
    # отправляем inline клавиатуру  для админа
    msg  = await message.answer(
        text=f"меню управления для администратора",
        reply_markup=get_menu_keyboard_for_admin_chat()
    )
    add_message(global_msg_fast, user_id, msg)
    add_message(global_msg_fast, user_id, message)
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
    if call.data == AdminChatButtons.BUTTON1.value.lower():
        await call.message.answer(f"Заглушка метод - ответ на кнопку {AdminChatButtons.BUTTON1.value}")
        return

    if call.data == AdminChatButtons.BUTTON2.value.lower():
        await call.message.answer(f"Заглушка метод - ответ на кнопку {AdminChatButtons.BUTTON2.value}")
        return

    if call.data == AdminChatButtons.BUTTON_FOR_INSERT_ANYTHING.value.lower():
        await set_waiting_input(
            state, bot, chat_id, user_id,
            command_name=AdminChatButtons.BUTTON_FOR_INSERT_ANYTHING.name.lower(),
            timeout=config.TIME_TO_INPUT_MSG_FSM
        )
        msg = await bot.send_message(
            chat_id,
            f"это заглушка - типовой ответ на {AdminChatButtons.BUTTON_FOR_INSERT_ANYTHING.value}я готов принять от вас инфу и что-то с ней делать",
            reply_markup=get_cancel_keyboard()
        )
        add_message(global_msg_fast, user_id, msg)
        # далее надо вызвать метод в блоке где ловятся waiting_inputs который что-то сделает с этой инфой
        return



