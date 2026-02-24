# message_handlers.py
import logging

from aiogram import types, F

from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext

from handlers.sub_handlers.admin_group_handler import handle_callback_from_admin_bot, some_method_msg_from_admin_chat, \
    some_method_text_msg_from_modertor
from handlers.sub_handlers.developer_chat_handler import some_method_msg_from_develop
from handlers.sub_handlers.main_menu_handler import handle_callback_main_menu_for_users
from handlers.sub_handlers.edit_profile_handler import handle_edit_profile_callbacks
from handlers.sub_handlers.deal_process_handler import handle_deal_process_callbacks

from entity.Enums_entity import UserFields, UserLifecycleStatus
from initApp.config_loader import config
from services.comands.developer_commands.standart_comands import save_actual_data
from services.comands.users_commands.for_contacted.contacted_menu_inline_handler import \
    handle_profile_registration_callbacks
from services.comands.users_commands.for_contacted.to_set_profile_commands import extract_and_save_full_name_from_msg, \
    extract_and_save_area, extract_and_save_product_name, extract_and_save_description, extract_and_save_price, \
    extract_and_save_socials
from services.comands.users_commands.edit_profile_commands import extract_and_update_name, extract_and_update_area, \
    extract_and_update_product_name, extract_and_update_description, extract_and_update_price
from services.comands.users_commands.sub_process1.extract_info_from_msg_procces1 import extract_text_info_from_msg
from services.keyboards.bot_all_buttons import AdminChatButtons, CommandsBot, MainMenuButtons, SubprocessMenu, \
    CONTACTED_Menu, ProfileRegistration_Menu, ModeratorChatButtons, EditProfileButtons, DealProcessButtons, ReviewProcessButtons
from services.keyboards.creator_inline_keyboards import get_inline_keyboard_menu_for_users
from services.msgs_utils.check_mandatory_reviews import check_and_enforce_unreviewed_deals
from services.users_utils.all_users_manager import get_all_users
from services.comands.users_commands.start_user import start_command_logic
from services.comands.users_commands.for_contacted.contacted_menu_text_handler import handle_contacted_menu_text_commands
from services.keyboards.creator_persistent_keyboards import get_cancel_keyboard, get_persistent_main_menu
from services.msgs_utils.cheking_chat_info import is_chat
from services.msgs_utils.deleter_messages import clear_messages
from services.msgs_utils.prepared_massages import menu_msg, menu_msg_for_devs, first_start_message

from services.send_msg_utils.utuls_send_msg import safe_send_message
from services.state_bot.global_store import FSM, global_msg_fast, add_message, global_msg_contacted_fast, \
    global_msg_for_close
from services.users_utils.all_users_manager import register_and_check_user, get_all_users
from services.users_utils.check_blocked import check_blocked_user

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

        user_id = message.from_user.id
        
        # --- Check Blocked ---
        if await check_blocked_user(user_id, bot, message):
            return

        # Получаем данные состояния
        data = await state.get_data()
        current_command = data.get("current_command")
    
        # --- Check Mandatory Review ---
        if await check_and_enforce_unreviewed_deals(user_id, bot, message, is_callback=False, current_data=current_command):
             return
        
        """для админ чата"""
        if current_command == AdminChatButtons.BUTTON_FOR_INSERT_ANYTHING.name.lower():
            await extract_text_info_from_msg(message, state, user_id)

            """для инфы анкеты"""
        elif current_command == ProfileRegistration_Menu.ENTER_NAME.value.lower():
            await extract_and_save_full_name_from_msg(message, state, user_id)

        elif current_command == ProfileRegistration_Menu.ENTER_AREA.value.lower():
            await extract_and_save_area(message, state, user_id)

        elif current_command == ProfileRegistration_Menu.ENTER_NAME_PRODUCT.value.lower():
            await extract_and_save_product_name(message, state, user_id)

        elif current_command == ProfileRegistration_Menu.ENTER_FULL_INFO_PRODUCT.value.lower():
            await extract_and_save_description(message, state, user_id)

        elif current_command == ProfileRegistration_Menu.ENTER_PRICE.value.lower():
            await extract_and_save_price(message, state, user_id)

        elif current_command == ProfileRegistration_Menu.ENTER_SOCIALS.value.lower():
            await extract_and_save_socials(message, state, user_id)

        elif current_command == ProfileRegistration_Menu.REJECT.name.lower():
             from services.comands.admin_commands.moderator_actions import process_rejection_reason
             await process_rejection_reason(message, state, bot)

        elif current_command == "reject_changes_reason":
             from services.comands.admin_commands.moderator_actions import process_rejection_changes_reason
             await process_rejection_changes_reason(message, state, bot)

        elif current_command == ModeratorChatButtons.EXCLUDE_PARTICIPANT.name.lower():
            from services.comands.admin_commands.exclude_participant import process_exclude_participant_input
            await process_exclude_participant_input(message, state, bot)

        elif current_command == ModeratorChatButtons.SEND_COINS.name.lower():
            from services.comands.admin_commands.send_coins import process_send_coins_input
            await process_send_coins_input(message, state, bot)

        elif current_command == ModeratorChatButtons.ROLLBACK_DEAL.name.lower():
            from services.comands.admin_commands.rollback_deal_command import process_rollback_deal_input
            await process_rollback_deal_input(message, state, bot)

        # для ввода от юзеров бота со статусом клиент (редактирование профиля)
        elif current_command == EditProfileButtons.EDIT_NAME.value.lower():
            await extract_and_update_name(message, state, user_id)

        elif current_command == EditProfileButtons.EDIT_AREA.value.lower():
            await extract_and_update_area(message, state, user_id)

        elif current_command == EditProfileButtons.EDIT_NAME_PRODUCT.value.lower():
            await extract_and_update_product_name(message, state, user_id)

        elif current_command == EditProfileButtons.EDIT_FULL_INFO_PRODUCT.value.lower():
            await extract_and_update_description(message, state, user_id)

        elif current_command == EditProfileButtons.EDIT_PRICE.value.lower():
            await extract_and_update_price(message, state, user_id)

        elif current_command == ReviewProcessButtons.ADD_TEXT_REVIEW.name.lower():
            from services.comands.users_commands.review_text_commands import extract_and_save_review_text
            await extract_and_save_review_text(message, state, user_id)

        """для ввода от юзеров бота со статусом клиент"""


"""
--- Обработчик callback кнопок ---
"""
async def handle_callback(call: CallbackQuery, bot, state: FSMContext):
    try:
        user_id = call.from_user.id
        chat_id = call.message.chat.id
        
        # --- Check Blocked ---
        if await check_blocked_user(user_id, bot, call):
            return

        # --- Check Mandatory Review ---
        if await check_and_enforce_unreviewed_deals(user_id, bot, call, is_callback=True, current_data=call.data):
            return


        if call.data == CommandsBot.CLOSE.value.lower():
            await call.answer("❌закрываю")
            await clear_messages(user_id, global_msg_fast, global_msg_for_close)
            return

        if is_chat(call.message, [config.DEVELOPER_CHAT_ID]):
            """ТОЛЬКО ДЛЯ ЧАТА разработчика"""
            if call.data == CommandsBot.STOP_BOT.value.lower():
                await save_actual_data(bot, user_id)
                return


        if is_chat(call.message, [config.MODERATOR_CONTACT_ID]):
            """ТОЛЬКО ДЛЯ админов которые управляют ботом  от имени компании"""
            await handle_callback_from_admin_bot(call, state, bot)


            """ТОЛЬКО ДЛЯ админов которые управляют ботом  от имени компании"""
        # elif call.data == CommandsBot.MENU.value.lower():
        #     await clear_messages(user_id, global_msg_fast)
        #     msg = await call.message.answer(
        #         menu_msg,
        #         reply_markup=get_inline_keyboard_menu_for_users()
        #     )
        #     add_message(global_msg_fast, user_id, msg)
        #     return

        # Обработка кнопок из MainMenuButtons
        if (
            call.data in [item.name.lower() for item in MainMenuButtons] or
            call.data.startswith(f"{MainMenuButtons.FIND_SERVICE.name.lower()}_") or
            call.data.startswith(f"{MainMenuButtons.REVIEWS.name.lower()}_") or
            call.data.startswith(f"{MainMenuButtons.CREATE_DEAL.name.lower()}_") or
            call.data.startswith(f"{MainMenuButtons.ACCEPT_TERMS.name.lower()}_") or
            call.data.startswith(f"{MainMenuButtons.ACCEPT_REQUEST.name.lower()}_") or
            call.data.startswith(f"{MainMenuButtons.REJECT_REQUEST.name.lower()}_")
        ):
            await handle_callback_main_menu_for_users(call, bot, state)
            return

        # Обработка кнопок из EditProfileButtons
        if call.data in [item.name.lower() for item in EditProfileButtons]:
            await handle_edit_profile_callbacks(bot, call, state)
            return

        # Обработка кнопок регистрации профиля
        if call.data in [item.name.lower() for item in ProfileRegistration_Menu]:
            await handle_profile_registration_callbacks(bot, call, user_id, state)
            return

        # Обработка кнопок из DealProcessButtons
        if call.data.startswith(f"{DealProcessButtons.CANCEL_DEAL.name.lower()}_") or \
           call.data.startswith(f"{DealProcessButtons.SERVICE_DONE.name.lower()}_"):
            await handle_deal_process_callbacks(call, bot, state)
            return

        # Обработка кнопок отзывов (ReviewProcessButtons + LEAVE_REVIEW)
        if any(call.data.startswith(f"{btn.name.lower()}_") for btn in ReviewProcessButtons) or \
           call.data.startswith(f"{DealProcessButtons.LEAVE_REVIEW.name.lower()}_") or \
           call.data.startswith(f"{DealProcessButtons.LEAVE_REVIEW_CLIENT.name.lower()}_"):
            from handlers.sub_handlers.review_process_handler import handle_review_callbacks
            await handle_review_callbacks(call, bot, state)
            return

    except Exception as e:
        logging.exception(f"Ошибка при обработке кнопки: {e}")
        await call.message.answer(f"⚠️ Ошибка при обработке кнопки: {e}")



async def handler_comands_or_simple_msg(message: Message, bot):
    user_id = message.from_user.id
    
    # --- Check Blocked ---
    if await check_blocked_user(user_id, bot, message):
         return

    # --- Check Mandatory Review ---
    if await check_and_enforce_unreviewed_deals(user_id, bot, message, is_callback=False, current_data=""):
         return

    text = (message.text or "").casefold()  # нормализуем сразу


    """проверка — сообщение из любого чата"""
    # --- START ---
    if text == CommandsBot.START.value.lower():
        await start_command_logic(message, bot)
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

    # --- CONTACTED MENU ---
    # Проверяем, есть ли текст сообщения в списке значений кнопок CONTACTED_Menu
    elif text in [c.value.lower() for c in CONTACTED_Menu]:
        await handle_contacted_menu_text_commands(message, bot)
        return


    if message.chat.id == config.ADMIN_CHAT_GROUP:
        """проверка — сообщение из админской группы?"""
        await some_method_msg_from_admin_chat(message)
        return


    elif message.chat.id == config.MODERATOR_CONTACT_ID:
        """проверка — сообщение от человека который управляет - модератор бота - то есть ответ на любые текстовые команды с админ чата"""
        await some_method_text_msg_from_modertor(message)
        return

    elif message.chat.id == config.DEVELOPER_CHAT_ID:
        """проверка — сообщение от девелопера"""
        await some_method_msg_from_develop(message)
        return


    # # todo проверить условие ниже
    # elif text in [c.value.lower() for c in CommandsBot] or text in [c.value for c in AdminChatButtons]\
    #         or text in [c.value for c in MainMenuButtons] or text in [c.value for c in SubprocessMenu]:
    #     """Другие команды если случайно текстовая команда бота прилетит которая не обрабатывается еще чтоб в ии не уходила"""

    #     msg = await message.answer(
    #         text="🤖",
    #         reply_markup=get_persistent_main_menu()
    #     )
    #     msg1 = await message.answer(
    #         text=f"Воспользуйтесь кнопками для заказа - они есть в --{CommandsBot.MENU.value}--"
    #     )
    #     add_message(global_msg_fast, user_id, msg)
    #     add_message(global_msg_fast, user_id, msg1)
    #     return



    else:
        """ Свободный текст / голос """
        await clear_messages(user_id, global_msg_fast)
        
        # Загружаем инфу о пользователе
        users_db = get_all_users()
        user_data = users_db.get(user_id) or users_db.get(str(user_id)) or {}
        user_status = user_data.get(UserFields.STATUS.value)
        
        # Если статус == client, показываем клавиатуру. Иначе — нет.
        if user_status == UserLifecycleStatus.CLIENT.value:
            reply_markup_to_send = get_persistent_main_menu()
        else:
            reply_markup_to_send = None
            
        msg1 = await message.answer(
            text=f"Я пока не умею отвечать на свободный текст - воспользуйтесь кнопками  - они есть в --{CommandsBot.MENU.value}--",
            reply_markup=reply_markup_to_send
        )
        add_message(global_msg_fast, user_id, msg1)
        return
        # await get_answer_to_simple_text_from_AI(message, text, user_id)
