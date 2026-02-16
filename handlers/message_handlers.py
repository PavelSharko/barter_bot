# message_handlers.py
import logging

from aiogram import types, F

from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext

from handlers.sub_handlers.admin_group_handler import some_method_msg_from_group_admin, \
    some_method_msg_from_admin, handle_callback_from_admin_bot
from handlers.sub_handlers.developer_chat_handler import some_method_msg_from_develop

from initApp.config_loader import config
from pictures.pictures_DB import START_PHOTO_ID
from services.AIHelpUtils.prepearer_response_to_AI import get_answer_to_simple_text_from_AI
from services.comands.developer_commands.standart_comands import save_actual_data
from services.comands.users_commands.sub_process1.extract_info_from_msg_procces1 import extract_text_info_from_msg
from services.keyboards.bot_all_buttons import AdminChatButtons, CommandsBot, MainMenuButtons, SubprocessMenu
from services.keyboards.creator_inline_keyboards import get_inline_keyboard_menu_for_users

from services.keyboards.creator_persistent_keyboards import get_persistent_main_menu, get_cancel_keyboard
from services.msgs_utils.cheking_chat_info import is_chat
from services.msgs_utils.deleter_messages import clear_messages
from services.msgs_utils.prepared_massages import menu_msg, menu_msg_for_devs, first_start_message

from services.send_msg_utils.utuls_send_msg import safe_send_message
from services.state_bot.global_store import FSM, global_msg_fast, add_message
from services.users_utils.all_users_manager import register_and_check_user, get_all_users

from handlers.fsm_utils import set_waiting_input
from aiogram.types import CallbackQuery, Message



def register_handlers(dp, bot):
    """
    ВСЕ callback_query вызываются тут через фасад handle_callback
    """
    @dp.callback_query()
    async def callback_query_handler(call: CallbackQuery, state: FSMContext):
        await handle_callback(call, bot, state)

    """
    ВСЕ ЧТО ПРИЛЕТАЕТ В ЧАТ КАК ТЕКСТ(исключение waiting_input)  вызываются тут 
    через фасад handler_comands_or_simple_msg
    """
    @dp.message(
        (F.text | F.voice),
        ~StateFilter(FSM.waiting_input),
    )
    async def universal_handler(message: Message):
        await handler_comands_or_simple_msg(message, bot)



    """
    ВСЕ ЧТО ПРИЛЕТАЕТ В ЧАТ КАК ТЕКСТ когда бот ждет  waiting_input
    вызываются тут 
    """
    @dp.message(FSM.waiting_input)
    async def universal_input_handler(message: types.Message, state: FSMContext):
        # todo создать фасад чтобы срань эту убрать которая тут будет если все в куче отловить

        # Получаем данные состояния
        data = await state.get_data()
        current_command = data.get("current_command")
        user_id = message.from_user.id

        """для админ чата"""
        if current_command == AdminChatButtons.BUTTON_FOR_INSERT_ANYTHING.name.lower():
            await extract_text_info_from_msg(message, state, user_id)

            """для всех чатов"""
        elif current_command == MainMenuButtons.EX_BUTTON_FOR_INSERT_ANYTHING.name.lower():
            await extract_text_info_from_msg(message, state, user_id)






"""
--- Обработчик callback кнопок ---
"""
async def handle_callback(call: CallbackQuery, bot, state: FSMContext):
    try:
        user_id = call.from_user.id
        chat_id = call.message.chat.id


        if is_chat(call.message, [config.DEVELOPER_CHAT_ID]):
            """ТОЛЬКО ДЛЯ   ЧАТА разработчика"""
            if call.data == CommandsBot.STOP_BOT.value.lower():
                await save_actual_data(bot, user_id)



        elif is_chat(call.message, [config.MODERATOR_CONTACT_ID]):
            """ТОЛЬКО ДЛЯ админов которые управляют ботом  от имени компании"""
            await handle_callback_from_admin_bot(call, state, bot)



        elif call.data == CommandsBot.CLOSE.value.lower():
            """команды  для всех"""
            await call.answer("❌закрываю")
            await clear_messages(user_id, global_msg_fast)
            return

        elif call.data == CommandsBot.MENU.value.lower():
            await clear_messages(user_id, global_msg_fast)
            msg = await call.message.answer(
                menu_msg,
                reply_markup=get_inline_keyboard_menu_for_users()
            )
            add_message(global_msg_fast, user_id, msg)
            return

        elif call.data == MainMenuButtons.EX_BUTTON1.value.lower():
            """команды  для всех"""
            await call.answer("✅принято")
            msg = await call.message.answer(f"Заглушка метод - ответ на кнопку {MainMenuButtons.EX_BUTTON1.value}")
            add_message(global_msg_fast, user_id, msg)
            return

        elif call.data == MainMenuButtons.EX_BUTTON2.value.lower():
            """команды  для всех"""
            await call.answer("✅принято")
            msg = await call.message.answer(f"Заглушка метод - ответ на кнопку {MainMenuButtons.EX_BUTTON2.value}")
            add_message(global_msg_fast, user_id, msg)
            return






        elif call.data == AdminChatButtons.BUTTON_FOR_INSERT_ANYTHING.value.lower():
            """ТАК ВЫЗЫВАЮТСЯ КОМАНДЫ ПОСЛЕ КОТОРЫХ НАДО ОБРАБОТАТЬ ДАННЫЕ КОТОРЫЕ ОТПРАВИТ ПОЛЬЗОВАТЕЛЬ"""
            await set_waiting_input(
                state, bot, chat_id, user_id,
                command_name=MainMenuButtons.EX_BUTTON_FOR_INSERT_ANYTHING.name.lower(),
                timeout=config.TIME_TO_INPUT_MSG_FSM
            )
            msg = await bot.send_message(
                chat_id,
                f"это заглушка - типовой ответ на {MainMenuButtons.EX_BUTTON_FOR_INSERT_ANYTHING.value}я готов принять от вас инфу и что-то с ней делать",
                reply_markup=get_cancel_keyboard()
            )
            add_message(global_msg_fast, user_id, msg)
            # далее надо вызвать метод в блоке где ловятся waiting_inputs который что-то сделает с этой инфой
            return

    except Exception as e:
        logging.exception(f"Ошибка при обработке кнопки: {e}")
        await call.message.answer(f"⚠️ Ошибка при обработке кнопки: {e}")



async def handler_comands_or_simple_msg(message: Message, bot):
    user_id = message.from_user.id
    text = (message.text or "").casefold()  # нормализуем сразу


    """проверка — сообщение из любого чата"""
    # --- START ---
    if text == CommandsBot.START.value.lower():
        all_users = get_all_users()
        if user_id not in all_users:
            # Новый пользователь → регистрируем как "оплатил"
            await register_and_check_user(user_id, bot)
            await bot.send_message(
                chat_id=user_id,
                text=first_start_message,
                reply_markup=get_persistent_main_menu()
            )
        else:
            # Уже есть в базе
            await bot.send_message(
                chat_id=user_id,
                text=first_start_message,
                reply_markup=get_persistent_main_menu()
            )
        return

    # --- MENU ---
    elif text == CommandsBot.MENU.value.lower():
        add_message(global_msg_fast, user_id, message)
        await clear_messages(user_id, global_msg_fast)
        msg = await message.answer(
            menu_msg,
            reply_markup=get_inline_keyboard_menu_for_users()
        )
        add_message(global_msg_fast, user_id, msg)
        return


    if message.chat.id == config.ADMIN_CHAT_GROUP:
        """проверка — сообщение из админской группы?"""
        await some_method_msg_from_group_admin(message)
        return


    elif message.chat.id == config.MODERATOR_CONTACT_ID:
        """проверка — сообщение от человека который управляет - модератор бота - то есть ответ на любые текстовые команды с админ чата"""
        await some_method_msg_from_admin(message)
        return

    elif message.chat.id == config.DEVELOPER_CHAT_ID:
        """проверка — сообщение от девелопера"""
        await some_method_msg_from_develop(message)
        return



    elif text in [c.value.lower() for c in CommandsBot] or text in [c.value for c in AdminChatButtons]\
            or text in [c.value for c in MainMenuButtons] or text in [c.value for c in SubprocessMenu]:
        """Другие команды если случайно текстовая команда бота прилетит которая не обрабатывается еще чтоб в ии не уходила"""

        msg = await message.answer(
            text="🤖",
            reply_markup=get_persistent_main_menu()
        )
        msg1 = await message.answer(
            text=f"Воспользуйтесь кнопками для заказа - они есть в --{CommandsBot.MENU.value}--"
        )
        add_message(global_msg_fast, user_id, msg)
        add_message(global_msg_fast, user_id, msg1)
        return



    else:
        """ Свободный текст / голос """
        # await get_answer_to_simple_text_from_AI(message, text, user_id)
