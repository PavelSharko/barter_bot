from services.state_bot.global_store import add_message, global_msg_fast
from aiogram import types
from aiogram.fsm.context import FSMContext


from handlers.fsm_utils import check_cancel_input, clear_waiting_input


from services.keyboards.creator_persistent_keyboards import get_persistent_main_menu



async def extract_text_info_from_msg(message: types.Message, state: FSMContext, user_id):
    # проверка что в сообщении есть текст
    text = (message.text or "").strip()
    if not text:
        msg = await message.answer("Вы не ввели текст - введите его")
        add_message(global_msg_fast, user_id, msg)
        return

    # проверка что не отменили ввод команды текста
    if await check_cancel_input(text, message, state):
        return

    # далее какая-то логика со введенным текстом -пока заглушка

    await message.answer(
        f"✅ четко вы ввели!\n\n{text}\n\n я могу его запомнить или что то с ним сделать -сохранить -\n "
        f" вам надо писать еще логику в коле бота",
        reply_markup=get_persistent_main_menu()
    )

    # сбрасываем ожидание ввода waiting_input чтобы он больше не срабатывал на считывание данных пока не попросим снова
    await clear_waiting_input(state, message.chat.id, user_id)