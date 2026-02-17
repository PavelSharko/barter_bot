from aiogram import Bot
from aiogram.types import Message

from entity.Enums_entity import UserFields, UserLifecycleStatus
from initApp.config_loader import config
from services.keyboards.creator_persistent_keyboards import get_persistent_main_menu
from services.keyboards.keyboards_for_CONTACTED import get_contacted_keyboard
from services.keyboards.keyboards_for_registration import get_rejected_keyboard
from services.msgs_utils.prepared_massages import first_start_message
from services.users_utils.all_users_manager import get_all_users, register_and_check_user
from services.state_bot.global_store import add_message, global_msg_contacted_fast


async def start_command_logic(message: Message, bot: Bot):
    """
    Логика обработки команды /start.
    """
    user_id = message.from_user.id
    all_users = get_all_users()

    # 1. Новый пользователь
    if user_id not in all_users:
        await register_and_check_user(user_id, bot)
        # Отправляем "Вы зарегистрировались"
        msg = await bot.send_message(
            chat_id=user_id,
            text="Вы зарегистрировались ✅"
        )
        add_message(global_msg_contacted_fast, user_id, msg)
        
        # Отправляем приветствие + клавиатуру для CONTACTED
        msg = await bot.send_message(
            chat_id=user_id,
            text=first_start_message,
            reply_markup=get_contacted_keyboard()
        )
        add_message(global_msg_contacted_fast, user_id, msg)
        return

    # 2. Пользователь уже есть - проверяем статус
    user_data = all_users[user_id]
    status = user_data.get(UserFields.STATUS.value, UserLifecycleStatus.CONTACTED.value)

    if status == UserLifecycleStatus.CONTACTED.value:
        msg = await bot.send_message(
            chat_id=user_id,
            text=first_start_message,
            reply_markup=get_contacted_keyboard()
        )
        add_message(global_msg_contacted_fast, user_id, msg)

    elif status == UserLifecycleStatus.CANDIDATE.value:
        msg = await bot.send_message(
            chat_id=user_id,
            text=f"{first_start_message}\n\n⏳ Ваша анкета на проверке."
        )
        add_message(global_msg_contacted_fast, user_id, msg)

    elif status == UserLifecycleStatus.CLIENT.value:
        msg = await bot.send_message(
            chat_id=user_id,
            text=first_start_message,
            reply_markup=get_persistent_main_menu()
        )
        add_message(global_msg_contacted_fast, user_id, msg)

    elif status == UserLifecycleStatus.REJECTED.value:
        # todo: добавить причину отказа из БД
        reason = "Причина не указана"
        msg = await bot.send_message(
            chat_id=user_id,
            text=f"🚫 Ваша анкета была отклонена.\nПричина: {reason}\n\nДля повторной подачи заявки очистите анкету и начните заполнение заново.",
            reply_markup=get_rejected_keyboard()
        )
        add_message(global_msg_contacted_fast, user_id, msg)

    elif status == UserLifecycleStatus.BLOCKED.value:
        msg = await bot.send_message(
            chat_id=user_id,
            text=f"⛔️ Вы были заблокированы.\nДля уточнения деталей напишите модератору {config.MODERATOR_USERNAME}"
        )
        add_message(global_msg_contacted_fast, user_id, msg)
