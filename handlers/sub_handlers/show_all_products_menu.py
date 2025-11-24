from services.comands.users_commands.sub_process1.info_product_maker import send_product1_info, send_product2_info, \
    send_product3_info
from services.keyboards.bot_all_buttons import SubprocessMenu
from services.msgs_utils.deleter_messages import clear_messages
from services.state_bot.global_store import global_msg_fast


async def handle_callback_all_products_menu(bot, call, user_id):
    """
    Обработка всех кнопок меню продуктов
    """
    await clear_messages(user_id, global_msg_fast)

    mapping = {
        SubprocessMenu.PRODUCT1.name.lower(): send_product1_info,
        SubprocessMenu.PRODUCT2.name.lower(): send_product2_info,
        SubprocessMenu.PRODUCT3.name.lower(): send_product3_info,

    }

    handler = mapping.get(call.data)
    if handler:
        await handler(bot, user_id)

