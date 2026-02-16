from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from handlers.fsm_utils import set_waiting_input
from initApp.config_loader import config
from services.keyboards.bot_all_buttons import ProfileRegistration_Menu
from services.keyboards.creator_persistent_keyboards import get_cancel_keyboard
from services.msgs_utils.deleter_messages import clear_messages
from services.state_bot.global_store import global_msg_contacted_fast, add_message


async def handle_profile_registration_callbacks(bot, call: CallbackQuery, user_id: int, state: FSMContext):
    """Обработчик всех колбеков регистрации профиля"""
    time_for_input_words = config.TIME_TO_INPUT_MSG_FSM
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    await clear_messages(user_id, global_msg_contacted_fast)


    if call.data == ProfileRegistration_Menu.ENTER_NAME.name.lower():
        await call.answer(text="Начинаем ввод ФИО ✅", show_alert=False)
        command_name = ProfileRegistration_Menu.ENTER_NAME.value.lower()
        await set_waiting_input(state, bot, chat_id, user_id, command_name, timeout=time_for_input_words)
        msg = await bot.send_message(
            chat_id=chat_id,
            text="🆔 Введите Свое ФИО»:",
            reply_markup=get_cancel_keyboard()
        )
        add_message(global_msg_contacted_fast, user_id, msg)
        return




    if call.data == ProfileRegistration_Menu.ENTER_AREA.name.lower():
        await call.answer(text="Указываем район 📍", show_alert=False)
        # логика для ENTER_REGION
        return

    if call.data == ProfileRegistration_Menu.ENTER_PRODUCT.name.lower():
        await call.answer(text="Указываем товар/услугу 🛒", show_alert=False)
        # логика для ENTER_PRODUCT
        return

    if call.data == ProfileRegistration_Menu.ENTER_PRICE.name.lower():
        await call.answer(text="Указываем прайс 💰", show_alert=False)
        # логика для ENTER_PRICE
        return
