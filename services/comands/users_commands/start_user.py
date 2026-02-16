from aiogram import Bot
from aiogram.types import Message

from entity.Enums_entity import UserFields, UserLifecycleStatus
from initApp.config_loader import config
from services.keyboards.creator_persistent_keyboards import get_persistent_main_menu
from services.keyboards.keyboards_for_CONTACTED import get_contacted_keyboard, get_rejected_keyboard
from services.msgs_utils.prepared_massages import first_start_message
from services.users_utils.all_users_manager import get_all_users, register_and_check_user


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
        await bot.send_message(
            chat_id=user_id,
            text="Вы зарегистрировались ✅"
        )
        # Отправляем приветствие + клавиатуру для CONTACTED
        await bot.send_message(
            chat_id=user_id,
            text=first_start_message,
            reply_markup=get_contacted_keyboard()
        )
        return

    # 2. Пользователь уже есть - проверяем статус
    user_data = all_users[user_id]
    status = user_data.get(UserFields.STATUS.value, UserLifecycleStatus.CONTACTED.value)

    if status == UserLifecycleStatus.CONTACTED.value:
        await bot.send_message(
            chat_id=user_id,
            text=first_start_message,
            reply_markup=get_contacted_keyboard()
        )

    elif status == UserLifecycleStatus.CANDIDATE.value:
        await bot.send_message(
            chat_id=user_id,
            text=f"{first_start_message}\n\n⏳ Ваша анкета на проверке."
        )

    elif status == UserLifecycleStatus.CLIENT.value:
        await bot.send_message(
            chat_id=user_id,
            text=first_start_message,
            reply_markup=get_persistent_main_menu()
        )

    elif status == UserLifecycleStatus.REJECTED.value:
        # todo: добавить причину отказа из БД
        reason = "Причина не указана"
        await bot.send_message(
            chat_id=user_id,
            text=f"🚫 Ваша анкета была отклонена.\nПричина: {reason}\n\nДля повторной подачи заявки очистите анкету и начните заполнение заново.",
            reply_markup=get_rejected_keyboard()
        )

    elif status == UserLifecycleStatus.BLOCKED.value:
        await bot.send_message(
            chat_id=user_id,
            text=f"⛔️ Вы были заблокированы.\nДля уточнения деталей напишите модератору {config.MODERATOR_USERNAME}"
        )
