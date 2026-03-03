from initApp.config_loader import config
from services.AIHelpUtils.connectorToAi import ask_n8n_agent_unic
from services.keyboards.sustem_inline_keyboard import get_inline_keyboard_close
from services.msgs_utils.deleter_messages import clear_messages
from services.state_bot.global_store import add_message, global_msg_fast


async def get_answer_to_simple_text_from_AI(message, text, user_id):
    query_json = {"type_query": text}
    url1 = config.STANDART_WEBHOOK_N8N_TEST
    url2 = config.STANDART_WEBHOOK_N8N_PROD

    msg0 = await message.answer("Секунду, уточняю... 🤔 Уже возвращаюсь!")
    add_message(global_msg_fast, user_id, msg0)


    try:
        response = await ask_n8n_agent_unic(url1, url2, query_json)
        answer = response.get("answer_from_ai")
        msg_text = answer if answer else "🤖 Нет ответа от ИИ, попробуйте позже."
    except RuntimeError:
        msg_text = "я сломался (ИИ недоступно) попробуй позже"

    await clear_messages(user_id, global_msg_fast)
    msg = await message.answer(msg_text, reply_markup=get_inline_keyboard_close())
    add_message(global_msg_fast, user_id, msg)
