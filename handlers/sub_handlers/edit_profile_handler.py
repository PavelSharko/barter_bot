from aiogram import Bot
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
import html

from services.keyboards.bot_all_buttons import EditProfileButtons, MainMenuButtons, ProcessChangingProfileButtons
from services.keyboards.sustem_inline_keyboard import get_inline_keyboard_close
from services.state_bot.global_store import add_message, global_msg_fast
from services.keyboards.edit_profile_keyboards import (
    get_edit_profile_menu_keyboard, get_keyboard_for_changing_profile,
    get_service_edit_keyboard, get_services_footer_keyboard
)
from services.msgs_utils.deleter_messages import clear_messages
from handlers.fsm_utils import set_waiting_input
from initApp.config_loader import config
from services.keyboards.creator_persistent_keyboards import get_cancel_keyboard, get_persistent_main_menu
from entity.Enums_entity import ChangesProfileStatus, UserFields, UserFlags, UserLifecycleStatus, UserProfileFields
from services.users_utils.all_users_manager import load_all_users, update_user_field


async def handle_edit_profile_callbacks(bot: Bot, call: CallbackQuery, state: FSMContext):
    """
    Обработчик кнопок редактирования профиля.
    """
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    data = call.data
    await clear_messages(call.from_user.id, global_msg_fast)

    # --- Проверка: профиль на проверке у модератора ---
    _all_users = load_all_users()
    _udata = _all_users.get(user_id) or _all_users.get(str(user_id)) or {}
    _changes_status = _udata.get(UserFlags.CHANGES_PROFILE_CONFIRMED.value)
    if _changes_status == ChangesProfileStatus.WAITING_CONFIRMATION.value:
        await call.answer()
        msg = await call.message.answer(
            "Вы уже внесли изменения и отправили на проверку анкету"
            "⏳ Сейчас модератор проверяет ваши новые данные "
            "Повтороное изменения профиля будет возможно после завершения проверки."
        )
        add_message(global_msg_fast, user_id, msg)
        return

    # 1. Меню редактирования — показ подтверждения
    if data == EditProfileButtons.EDIT_PROFILE_MENU.name.lower():

        from services.msgs_utils.prepared_massages import confirm_edit_profile_msg
        from services.keyboards.edit_profile_keyboards import get_confirm_edit_profile_keyboard
        await clear_messages(user_id, global_msg_fast)
        msg = await call.message.answer(
            confirm_edit_profile_msg,
            reply_markup=get_confirm_edit_profile_keyboard()
        )
        add_message(global_msg_fast, user_id, msg)
        await call.answer()
        return

    # 2. Подтверждение — вход в режим редактирования
    elif data == EditProfileButtons.CONFIRM_EDIT_PROFILE.name.lower():
        from services.users_utils.temp_profile_manager import copy_profile_to_temp

        # Копируем профиль во временный файл
        copy_profile_to_temp(user_id)

        # Устанавливаем статусы
        update_user_field(user_id, UserFields.STATUS.value, UserLifecycleStatus.TIMELY_PROFILE_CHANGE_BLOCKED.value)
        update_user_field(user_id, UserFlags.NOW_IS_TRY_CHANGING_PROFILE.value, True)

        await clear_messages(user_id, global_msg_fast)
        msg = await call.message.answer(
            "Вы в режиме редактирования профиля",
            reply_markup=get_keyboard_for_changing_profile()
        )
        add_message(global_msg_fast, user_id, msg)
        await call.answer()
        return

    # 3. Отмена редактирования (до входа в редактирование услуги)
    elif data == EditProfileButtons.CANCEL_EDIT_PROFILE.name.lower():
        await clear_messages(user_id, global_msg_fast)
        await call.answer("принято🔫🔫🔫")
        return

    # 4. Завершение редактирования
    elif data == EditProfileButtons.SAVE_CHANGES.name.lower() or data == ProcessChangingProfileButtons.FINISH_EDITING.name.lower():
        from services.keyboards.edit_profile_keyboards import get_moderator_approval_changes_keyboard
        from services.users_utils.temp_profile_manager import (
            freeze_temp_profile, delete_temp_profile, has_profile_changes,
            build_diff_text, get_new_profile
        )

        changed = has_profile_changes(user_id)

        if not changed:
            # Ничего не изменено — просто выходим
            delete_temp_profile(user_id)
            update_user_field(user_id, UserFlags.NOW_IS_TRY_CHANGING_PROFILE.value, False)
            update_user_field(user_id, UserFields.STATUS.value, UserLifecycleStatus.CLIENT.value)

            await call.answer()
            await clear_messages(user_id, global_msg_fast)
            msg = await call.message.answer(
                "Вы не внесли изменений. Режим редактирования завершён."
            )
            add_message(global_msg_fast, user_id, msg)
            return

        # Фиксируем: editing → {new, old}. Данные в основной файл НЕ переносятся до решения модератора.
        freeze_temp_profile(user_id)

        # Снимаем флаг редактирования, ставим статус ожидания подтверждения
        update_user_field(user_id, UserFlags.NOW_IS_TRY_CHANGING_PROFILE.value, False)
        update_user_field(user_id, UserFlags.CHANGES_PROFILE_CONFIRMED.value, ChangesProfileStatus.WAITING_CONFIRMATION.value)

        # Формируем diff для модератора
        new_profile = get_new_profile(user_id) or {}
        diff_text = build_diff_text(user_id)

        from services.msgs_utils.alert_formatter import format_profile_changed_alert
        from services.users_utils.user_profile_manager import load_profiles
        users_db = load_all_users()
        profiles_db = load_profiles()
        
        moderator_text = format_profile_changed_alert(
            user_id=user_id,
            username=call.from_user.username,
            diff_text=diff_text,
            users_db=users_db,
            profiles_db=profiles_db
        )

        MAX_LEN = 3500
        parts = []
        current_part = ""
        for line in moderator_text.split('\n'):
            if len(current_part) + len(line) + 1 > MAX_LEN:
                parts.append(current_part)
                current_part = line + '\n'
            else:
                current_part += line + '\n'
        if current_part.strip():
            parts.append(current_part)

        try:
            for i, part in enumerate(parts):
                markup = get_moderator_approval_changes_keyboard(user_id) if i == len(parts) - 1 else None
                await bot.send_message(
                    chat_id=config.MODERATOR_CONTACT_ID,
                    text=part,
                    parse_mode="HTML",
                    reply_markup=markup
                )
        except Exception as e:
            print(f"Ошибка отправки модератору: {e}")
            try:
                await bot.send_message(
                    chat_id=config.DEVELOPER_CHAT_ID,
                    text=f"🚨 <b>Ахтунг!</b> Ошибка отправки <b>ИЗМЕНЕННОЙ</b> анкеты модератору!\nUser ID: <code>{user_id}</code>\nОшибка: {html.escape(str(e))}",
                    parse_mode="HTML"
                )
            except Exception as e2:
                print(f"Даже разработчику не ушло: {e2}")

        await call.answer()
        await clear_messages(user_id, global_msg_fast)
        msg = await call.message.answer(
            "Ваши изменения отправлены на проверку модератору. "
            "Пока идёт проверка вы можете записываться на сделки, "
            "но не оказывать услуги — мы постараемся проверить побыстрее 🙏"
        )
        add_message(global_msg_fast, user_id, msg)
        return


    # 4.1. Отмена всех изменений

    elif data == ProcessChangingProfileButtons.CANCEL_CHANGES.name.lower():
        from services.users_utils.temp_profile_manager import delete_temp_profile

        delete_temp_profile(user_id)
        update_user_field(user_id, UserFlags.NOW_IS_TRY_CHANGING_PROFILE.value, False)
        update_user_field(user_id, UserFields.STATUS.value, UserLifecycleStatus.CLIENT.value)

        await call.answer()
        await clear_messages(user_id, global_msg_fast)

        msg = await call.message.answer(
            "Изменения отменены. Ваш профиль не был изменён."
        )
        add_message(global_msg_fast, user_id, msg)
        return

    # ========================================================
    # 5. Кнопки из ProcessChangingProfileButtons — простые поля
    # ========================================================

    # 5.1. Имя
    elif data == ProcessChangingProfileButtons.EDIT_NAME.name.lower():
        from services.users_utils.temp_profile_manager import get_temp_profile
        temp = get_temp_profile(user_id) or {}
        old_name = temp.get(UserProfileFields.NAME.value, "Не указано")
        prompt = f"Текущее имя: <b>{html.escape(str(old_name))}</b>\n\nВведите новое имя (ФИО, минимум 2 слова):"
        msg = await call.message.answer(prompt, parse_mode="HTML", reply_markup=get_cancel_keyboard())
        add_message(global_msg_fast, user_id, msg)
        await set_waiting_input(state, bot, chat_id, user_id, ProcessChangingProfileButtons.EDIT_NAME.value, timeout=config.TIME_TO_INPUT_MSG_FSM)
        await call.answer()
        return

    # 5.2. Район
    elif data == ProcessChangingProfileButtons.EDIT_AREA.name.lower():
        from services.users_utils.temp_profile_manager import get_temp_profile
        temp = get_temp_profile(user_id) or {}
        old_area = temp.get(UserProfileFields.AREA.value, "Не указано")
        prompt = f"Текущий район: <b>{html.escape(str(old_area))}</b>\n\nВведите новый район:"
        msg = await call.message.answer(prompt, parse_mode="HTML", reply_markup=get_cancel_keyboard())
        add_message(global_msg_fast, user_id, msg)
        await set_waiting_input(state, bot, chat_id, user_id, ProcessChangingProfileButtons.EDIT_AREA.value, timeout=config.TIME_TO_INPUT_MSG_FSM)
        await call.answer()
        return

    # 5.3. Деятельность
    elif data == ProcessChangingProfileButtons.EDIT_PROFESSION.name.lower():
        from services.users_utils.temp_profile_manager import get_temp_profile
        temp = get_temp_profile(user_id) or {}
        old_prof = temp.get(UserProfileFields.PROFESSION.value, "Не указано")
        prompt = f"Текущая деятельность: <b>{html.escape(str(old_prof))}</b>\n\nВведите новое название деятельности (от 2 до 50 символов):"
        msg = await call.message.answer(prompt, parse_mode="HTML", reply_markup=get_cancel_keyboard())
        add_message(global_msg_fast, user_id, msg)
        await set_waiting_input(state, bot, chat_id, user_id, ProcessChangingProfileButtons.EDIT_PROFESSION.value, timeout=config.TIME_TO_INPUT_MSG_FSM)
        await call.answer()
        return

    # 5.4. Описание (о себе)
    elif data == ProcessChangingProfileButtons.EDIT_DESCRIPTION.name.lower():
        from services.users_utils.temp_profile_manager import get_temp_profile
        temp = get_temp_profile(user_id) or {}
        old_desc = temp.get(UserProfileFields.DESCRIPTION_PROFESSION.value, "Не указано")
        prompt = f"Текущее описание:\n<i>{html.escape(str(old_desc))}</i>\n\nВведите новое описание (от 50 до 300 символов):"
        msg = await call.message.answer(prompt, parse_mode="HTML", reply_markup=get_cancel_keyboard())
        add_message(global_msg_fast, user_id, msg)
        await set_waiting_input(state, bot, chat_id, user_id, ProcessChangingProfileButtons.EDIT_DESCRIPTION.value, timeout=config.TIME_TO_INPUT_MSG_FSM)
        await call.answer()
        return

    # 5.5. Ссылки
    elif data == ProcessChangingProfileButtons.EDIT_SOCIALS.name.lower():
        from services.users_utils.temp_profile_manager import get_temp_profile
        temp = get_temp_profile(user_id) or {}
        old_links = temp.get(UserProfileFields.SOCIAL_LINKS.value, [])
        old_links_text = "\n".join(old_links) if old_links else "Не указано"
        prompt = f"Текущие ссылки:\n{html.escape(old_links_text)}\n\nВведите новые ссылки (от 1 до 10, через пробел или перенос строки):"
        msg = await call.message.answer(prompt, parse_mode="HTML", reply_markup=get_cancel_keyboard())
        add_message(global_msg_fast, user_id, msg)
        await set_waiting_input(state, bot, chat_id, user_id, ProcessChangingProfileButtons.EDIT_SOCIALS.value, timeout=config.TIME_TO_INPUT_MSG_FSM)
        await call.answer()
        return



    # ========================================================
    # 6. Услуги — показ списка
    # ========================================================
    elif data == ProcessChangingProfileButtons.EDIT_SERVICES.name.lower():
        from services.users_utils.temp_profile_manager import get_temp_profile

        temp = get_temp_profile(user_id) or {}
        services = temp.get(UserProfileFields.SERVICES.value, [])

        if not services:
            msg = await call.message.answer(
                "У вас пока нет услуг.\n\nХотите добавить услугу?",
                reply_markup=get_services_footer_keyboard()
            )
            add_message(global_msg_fast, user_id, msg)
            await call.answer()
            return

        for idx, s in enumerate(services):
            svc_name = html.escape(str(s.get('name', 'Услуга')))
            svc_desc = html.escape(str(s.get('description', 'Без описания')))
            svc_price = html.escape(str(s.get('price', '0')))
            text = (
                f"<b>Услуга {idx + 1} — {svc_name}</b>\n\n"
                f"{svc_desc}\n\n"
                f"Цена: {svc_price} 🪙"
            )
            msg = await call.message.answer(
                text,
                parse_mode="HTML",
                reply_markup=get_service_edit_keyboard(idx)
            )
            add_message(global_msg_fast, user_id, msg)

        # Футер: добавить услугу + назад
        msg = await call.message.answer(
            "Выберите услугу которую хотите отредактировать либо вернитесь назад.\n\nХотите добавить ещё услуги? Нажмите на кнопку 👇",
            reply_markup=get_services_footer_keyboard()
        )
        add_message(global_msg_fast, user_id, msg)
        await call.answer()
        return

    # 6.1. Назад к основному меню редактирования
    elif data == ProcessChangingProfileButtons.BACK_TO_EDIT_MENU.name.lower():
        await clear_messages(user_id, global_msg_fast)
        msg = await call.message.answer(
            "Вы в режиме редактирования профиля",
            reply_markup=get_keyboard_for_changing_profile()
        )
        add_message(global_msg_fast, user_id, msg)
        await call.answer()
        return

    # ========================================================
    # 7. Редактирование конкретной услуги
    # ========================================================
    elif data.startswith(f"{ProcessChangingProfileButtons.EDIT_SERVICE.name.lower()}_"):
        from services.users_utils.temp_profile_manager import get_temp_profile

        try:
            service_idx = int(data.split('_')[-1])
        except (ValueError, IndexError):
            await call.answer("Ошибка", show_alert=True)
            return

        temp = get_temp_profile(user_id) or {}
        services = temp.get(UserProfileFields.SERVICES.value, [])
        if service_idx >= len(services):
            await call.answer("Услуга не найдена", show_alert=True)
            return

        old_service = services[service_idx]
        old_name = html.escape(str(old_service.get('name', '')))

        # Сохраняем индекс редактируемой услуги в FSM
        await state.update_data(editing_service_idx=service_idx)

        await clear_messages(user_id, global_msg_fast)
        prompt = (
            f"Окей — приступим 🔧\n\n"
            f"Ранее услуга называлась: <b>{old_name}</b>\n"
            f"Введите новое название:"
        )
        msg = await call.message.answer(prompt, parse_mode="HTML", reply_markup=get_cancel_keyboard())
        add_message(global_msg_fast, user_id, msg)
        await set_waiting_input(state, bot, chat_id, user_id, ProcessChangingProfileButtons.EDIT_SERVICE_NAME_INPUT.value, timeout=config.TIME_TO_INPUT_MSG_FSM)
        # Восстанавливаем editing_service_idx после set_waiting_input (он делает state.clear)
        await state.update_data(editing_service_idx=service_idx)
        await call.answer()
        return

    # ========================================================
    # 8. Удаление услуги
    # ========================================================
    elif data.startswith(f"{ProcessChangingProfileButtons.DELETE_SERVICE.name.lower()}_"):
        from services.users_utils.temp_profile_manager import get_temp_profile, update_temp_profile

        try:
            service_idx = int(data.split('_')[-1])
        except (ValueError, IndexError):
            await call.answer("Ошибка", show_alert=True)
            return

        temp = get_temp_profile(user_id) or {}
        services = temp.get(UserProfileFields.SERVICES.value, [])

        if len(services) <= 1:
            await clear_messages(user_id, global_msg_fast)
            msg = await call.message.answer(
                "Вы не можете удалить последнюю услугу. Для этого добавьте одну новую, "
                "чтобы после удаления осталась минимум одна услуга.",
                reply_markup=get_keyboard_for_changing_profile()
            )
            add_message(global_msg_fast, user_id, msg)
            await call.answer()
            return

        if service_idx < len(services):
            services.pop(service_idx)
            update_temp_profile(user_id, {UserProfileFields.SERVICES.value: services})

        await clear_messages(user_id, global_msg_fast)
        msg = await call.message.answer(
            "Отлично, услуга была удалена ✅",
            reply_markup=get_keyboard_for_changing_profile()
        )
        add_message(global_msg_fast, user_id, msg)
        await call.answer()
        return

    # ========================================================
    # 9. Добавление новой услуги
    # ========================================================
    elif data == ProcessChangingProfileButtons.ADD_SERVICE.name.lower():
        await clear_messages(user_id, global_msg_fast)
        prompt = "Введите название новой услуги (от 2 до 50 символов):"
        msg = await call.message.answer(prompt, reply_markup=get_cancel_keyboard())
        add_message(global_msg_fast, user_id, msg)
        await set_waiting_input(state, bot, chat_id, user_id, ProcessChangingProfileButtons.ADD_SERVICE_NAME_INPUT.value, timeout=config.TIME_TO_INPUT_MSG_FSM)
        await call.answer()
        return

    # Если кнопка не распознана
    await bot.send_message(chat_id=user_id, text="Неизвестная кнопка")
    await call.answer()
