from services.keyboards.creator_inline_keyboards import get_menu_keyboard_for_developer
from services.keyboards.creator_persistent_keyboards import get_persistent_main_menu
from services.msgs_utils.deleter_messages import clear_messages
from services.state_bot.global_store import global_msg_fast, add_message


async def some_method_msg_from_develop(message):
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
    msg0 = await message.answer(
        text=f"🤖 ",
        reply_markup=get_persistent_main_menu()
    )
    # отправляем inline клавиатуру  для админа
    msg  = await message.answer(
        text=f"меню управления для разработчика",
        reply_markup=get_menu_keyboard_for_developer()
    )
    # add_message(global_msg_fast, user_id, msg0)
    add_message(global_msg_fast, user_id, msg)
    add_message(global_msg_fast, user_id, message)
    return
