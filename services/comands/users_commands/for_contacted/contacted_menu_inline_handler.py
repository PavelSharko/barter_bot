from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from handlers.fsm_utils import set_waiting_input
from initApp.config_loader import config
from services.keyboards.bot_all_buttons import ProfileRegistration_Menu
from services.keyboards.creator_persistent_keyboards import get_cancel_keyboard
from services.msgs_utils.deleter_messages import clear_messages
from services.msgs_utils.prepared_massages import info_about_product
from services.state_bot.global_store import global_msg_contacted_fast, add_message
from entity.Enums_entity import UserLifecycleStatus, UserFields
from services.users_utils.all_users_manager import load_all_users, save_all_users
from services.keyboards.keyboards_for_registration import get_moderator_approval_keyboard


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
            text="🆔 Введите Свое ФИО»:"
        )
        add_message(global_msg_contacted_fast, user_id, msg)
        return




    if call.data == ProfileRegistration_Menu.ENTER_AREA.name.lower():
        await call.answer(text="Указываем район 📍", show_alert=False)
        command_name = ProfileRegistration_Menu.ENTER_AREA.value.lower()
        await set_waiting_input(state, bot, chat_id, user_id, command_name, timeout=time_for_input_words)
        msg = await bot.send_message(
            chat_id=chat_id,
            text="📍 Напишите текстом район (один или несколько, или 'Весь остров'):"
        )
        add_message(global_msg_contacted_fast, user_id, msg)
        return

    if call.data == ProfileRegistration_Menu.ENTER_NAME_PROFESSION.name.lower():
        await call.answer(text="Указываем товар/услугу 🛒", show_alert=False)
        command_name = ProfileRegistration_Menu.ENTER_NAME_PROFESSION.value.lower()
        await set_waiting_input(state, bot, chat_id, user_id, command_name, timeout=time_for_input_words)
        msg = await bot.send_message(
            chat_id=chat_id,
            text="🛒 Скажите, как называется товар/услуга, которую вы предоставляете?"
        )
        add_message(global_msg_contacted_fast, user_id, msg)
        return

    if call.data == ProfileRegistration_Menu.ENTER_FULL_INFO_PROFESSION.name.lower():
        await call.answer(text="Описываем деятельность 📝", show_alert=False)
        command_name = ProfileRegistration_Menu.ENTER_FULL_INFO_PROFESSION.value.lower()
        await set_waiting_input(state, bot, chat_id, user_id, command_name, timeout=time_for_input_words)
        msg = await bot.send_message(
            chat_id=chat_id,
            text=(
                "📝 Расскажите о себе и своей деятельности (от 50 до 300 символов) — эту информацию увидят другие участники клуба, так что постарайся описать всё понятно и привлекательно 😊\n\n"
                "⚠️ Пожалуйста, не пишите здесь цены услуг — для них будет отдельный шаг."
            )
        )
        add_message(global_msg_contacted_fast, user_id, msg)
        return

    if call.data == ProfileRegistration_Menu.ADD_NAME_PRODUCT.name.lower():
        await call.answer(text="Название услуги 🛒", show_alert=False)
        command_name = ProfileRegistration_Menu.ADD_NAME_PRODUCT.value.lower()
        await set_waiting_input(state, bot, chat_id, user_id, command_name, timeout=time_for_input_words)
        msg = await bot.send_message(
            chat_id=chat_id,
            text="🛒 Введите название вашей конкретной услуги или товара:"
        )
        add_message(global_msg_contacted_fast, user_id, msg)
        return

    if call.data == ProfileRegistration_Menu.ADD_INFO_PRODUCT.name.lower():
        await call.answer(text="Описание услуги 📝", show_alert=False)
        command_name = ProfileRegistration_Menu.ADD_INFO_PRODUCT.value.lower()
        await set_waiting_input(state, bot, chat_id, user_id, command_name, timeout=time_for_input_words)
        msg = await bot.send_message(
            chat_id=chat_id,
            text=(
                "Теперь подробно, но кратко опишите детали услуги (что входит, нюансы). "
                "Также укажите условия отмены — за какое время вы готовы принять отмену без последствий (например: за час, за день, за неделю).\n\n"
                "⚠️ Пожалуйста, не пишите в этом разделе цену — для неё будет отдельный шаг."
            )
        )
        add_message(global_msg_contacted_fast, user_id, msg)
        return
        
    if call.data == ProfileRegistration_Menu.ALL_SERVICES_FILLED.name.lower():
        await call.answer(text="Переходим к ссылкам 🔗", show_alert=False)
        from services.keyboards.keyboards_for_registration import get_socials_keyboard
        msg = await bot.send_message(
            chat_id=chat_id,
            text="Вы добавили услуги. Теперь давайте перейдем к ссылкам. Нажмите на кнопку ниже:",
            reply_markup=get_socials_keyboard()
        )
        add_message(global_msg_contacted_fast, user_id, msg)
        return

    if call.data == ProfileRegistration_Menu.ENTER_PRICE.name.lower():
        await call.answer(text="Указываем прайс 💰", show_alert=False)
        command_name = ProfileRegistration_Menu.ENTER_PRICE.value.lower()
        await set_waiting_input(state, bot, chat_id, user_id, command_name, timeout=time_for_input_words)
        msg = await bot.send_message(
            chat_id=chat_id,
            text="💰 Укажите прайс:"
        )
        add_message(global_msg_contacted_fast, user_id, msg)
        return

    if call.data == ProfileRegistration_Menu.ENTER_SOCIALS.name.lower():
        await call.answer(text="Указываем ссылки 🔗", show_alert=False)
        command_name = ProfileRegistration_Menu.ENTER_SOCIALS.value.lower()
        await set_waiting_input(state, bot, chat_id, user_id, command_name, timeout=time_for_input_words)
        msg = await bot.send_message(
            chat_id=chat_id,
            text="🔗 Укажите ссылки на соцсети и отзывы:"
        )
        add_message(global_msg_contacted_fast, user_id, msg)
        return
        
    if call.data == ProfileRegistration_Menu.FINAL_PROFILE_VIEW.name.lower():
        await call.answer(text="Просмотр анкеты 👀", show_alert=False)
        
        from services.users_utils.user_profile_manager import get_profile
        from entity.Enums_entity import UserProfileFields
        from services.keyboards.keyboards_for_registration import get_profile_review_keyboard

        profile = get_profile(user_id) or {}
        
        # Формируем красивый текст
        text = "📋 <b>Ваша анкета:</b>\n\n"

        name = profile.get(UserProfileFields.NAME.value) or "Не указано"
        area = profile.get(UserProfileFields.AREA.value) or "Не указано"
        profession = profile.get(UserProfileFields.PROFESSION.value) or "Не указано"
        desc_prof = profile.get(UserProfileFields.DESCRIPTION_PROFESSION.value) or "Не указано"
        links = "\n".join(profile.get(UserProfileFields.SOCIAL_LINKS.value, [])) or "Не указано"

        text += f"<b>ФИО</b>: {name}\n"
        text += f"<b>Район</b>: {area}\n"
        text += f"<b>Деятельность</b>: {profession}\n"
        text += f"<b>О себе/Детали</b>: {desc_prof}\n\n"
        text += f"<b>Ссылки</b>:\n{links}\n\n"
        
        services = profile.get(UserProfileFields.SERVICES.value, [])
        if services:
            text += "<b>Ваши услуги:</b>\n"
            for i, s in enumerate(services, 1):
                text += f"{i}. <b>{s.get('name', '')}</b>\n"
                text += f"   <i>Описание</i>: {s.get('description', '')}\n"
                text += f"   <i>Прайс</i>: {s.get('price', '')}\n\n"
        else:
            text += "<b>Услуги отсутствуют.</b>\n"

        msg = await bot.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode="HTML",
            reply_markup=get_profile_review_keyboard()
        )

        add_message(global_msg_contacted_fast, user_id, msg)
        return

    if call.data == ProfileRegistration_Menu.RESTART_PROFILE.name.lower():
        await call.answer("Заполняем заново 🔄")
        from services.keyboards.keyboards_for_registration import get_full_name_keyboard
        msg = await bot.send_message(chat_id, "🔄 Хорошо, давайте заполним анкету заново. Введите ФИО:", reply_markup=get_full_name_keyboard())
        add_message(global_msg_contacted_fast, user_id, msg)
        # Сброс состояния? Можно, но extract_and_save_full_name очистит.
        return

    if call.data == ProfileRegistration_Menu.SEND_TO_REVIEW.name.lower():
        # 1. Обновляем статус пользователя
        users = load_all_users()
        if user_id in users:
            users[user_id][UserFields.STATUS.value] = UserLifecycleStatus.CANDIDATE.value
            save_all_users()

        # 2. Отправляем сообщение пользователю
        await call.answer("Отправлено на проверку 📮")
        msg = await bot.send_message(
            chat_id, 
            f"Спасибо, что заполнил анкету! 🙏\n\n"
            f"Мы передали её на проверку модератору — обычно это занимает немного времени. Как только анкета будет одобрена, ты получишь уведомление и доступ ко всем функциям клуба 🌴\n\n"
            f"Если тебе нужна помощь: {config.MODERATOR_USERNAME}"
        )
        add_message(global_msg_contacted_fast, user_id, msg)

        # 3. Отправляем уведомление модератору
        from services.users_utils.user_profile_manager import get_profile
        from entity.Enums_entity import UserProfileFields
        
        profile = get_profile(user_id) or {}
        
        name = profile.get(UserProfileFields.NAME.value) or "Не указано"
        area = profile.get(UserProfileFields.AREA.value) or "Не указано"
        profession = profile.get(UserProfileFields.PROFESSION.value) or "Не указано"
        desc_prof = profile.get(UserProfileFields.DESCRIPTION_PROFESSION.value) or "Не указано"
        links = "\n".join(profile.get(UserProfileFields.SOCIAL_LINKS.value, [])) or "Не указано"
        
        import html
        moderator_text = (
            f"🆕 <b>Новая заявка на вступление!</b>\n"
            f"ID: <code>{user_id}</code>\n"
            f"Username: @{html.escape(str(call.from_user.username))}\n\n"
            f"<b>ФИО</b>: {html.escape(str(name))}\n"
            f"<b>Район</b>: {html.escape(str(area))}\n"
            f"<b>Деятельность</b>: {html.escape(str(profession))}\n"
            f"<b>О себе</b>: {html.escape(str(desc_prof))}\n"
            f"<b>Ссылки</b>: \n{html.escape(str(links))}\n\n"
        )
        
        services = profile.get(UserProfileFields.SERVICES.value, [])
        if services:
            moderator_text += "<b>Услуги:</b>\n"
            for i, s in enumerate(services, 1):
                moderator_text += f"{i}. <b>{html.escape(str(s.get('name', '')))}</b>\n"
                moderator_text += f"   <i>Описание</i>: {html.escape(str(s.get('description', '')))}\n"
                moderator_text += f"   <i>Прайс</i>: {html.escape(str(s.get('price', '')))}\n\n"
        else:
            moderator_text += "<b>Услуги отсутствуют.</b>\n"

        # Отправляем модератору
        try:
            await bot.send_message(
                chat_id=config.MODERATOR_CONTACT_ID,
                text=moderator_text,
                parse_mode="HTML",
                reply_markup=get_moderator_approval_keyboard(user_id)
            )
        except Exception as e:
            print(f"Ошибка отправки модератору: {e}")
            
        return
