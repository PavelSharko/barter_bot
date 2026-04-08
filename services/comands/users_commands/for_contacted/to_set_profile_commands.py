from handlers.fsm_utils import check_cancel_input, clear_waiting_input
from services.keyboards.keyboards_for_registration import (
    get_area_keyboard, get_product_name_keyboard, get_product_desc_keyboard,
    get_price_keyboard, get_socials_keyboard, get_final_profile_keyboard, get_full_name_keyboard
)
from services.msgs_utils.deleter_messages import clear_messages
from services.state_bot.global_store import global_msg_contacted_fast, add_message, global_msg_fast
from services.users_utils.all_users_manager import load_all_users, save_all_users, get_all_users
from services.users_utils.user_profile_manager import create_or_update_profile, get_profile
from entity.Enums_entity import UserFields, UserProfileFields
import re

async def send_error(message, user_id, text):
    msg = await message.answer(f"❌ {text}")
    add_message(global_msg_contacted_fast, user_id, msg)

async def extract_and_save_full_name_from_msg(message, state, user_id):
    text = (message.text or "").strip()
    
    if not text:
        await send_error(message, user_id, "Нужен текст — картинки и файлы здесь не подойдут 🙏 Напиши словами!")
        return

    if await check_cancel_input(text, message, state):
        return

    # Валидация ФИО
    # Длина 2-100
    if not (2 <= len(text) <= 100):
        await send_error(message, user_id, "Ошибка: имя должно быть от 2 до 100 символов")
        return
    
    # Только буквы (кириллица/латиница), пробелы, дефисы
    if not re.match(r"^[a-zA-Zа-яА-ЯёЁ\s\-]+$", text):
        await send_error(message, user_id, "Ошибка: имя должно содержать только буквы, пробелы и дефис")
        return
        
    # Минимум 2 слова
    if len(text.split()) < 2:
        await send_error(message, user_id, "Ошибка: введите имя и фамилию (минимум 2 слова)")
        return

    # Сохраняем имя только в анкету
    await create_or_update_profile(user_id, {
        UserProfileFields.NAME.value: text
    })

    await clear_messages(user_id, global_msg_contacted_fast, global_msg_fast)
    await clear_waiting_input(state, message.chat.id, user_id)

    msg = await message.answer(
        text=f"✅ Отлично, {text}! Приятно познакомиться 😊\n\nТеперь скажи, пожалуйста — в каких районах ты работаешь? Можно указать несколько, весь остров или написать «онлайн» 🌍",
        reply_markup=get_area_keyboard()
    )
    add_message(global_msg_contacted_fast, user_id, msg)


async def extract_and_save_area(message, state, user_id):
    text = (message.text or "").strip()
    if await check_cancel_input(text, message, state): return
    
    # Валидация Района
    # Длина 2-50
    if not (2 <= len(text) <= 50):
         await send_error(message, user_id, "Ошибка: название района должно быть от 2 до 50 символов")
         return

    # Только буквы, пробелы, дефисы, запятые
    if not re.match(r"^[a-zA-Zа-яА-ЯёЁ\s\-,]+$", text):
        await send_error(message, user_id, "Ошибка: район должен содержать только буквы, пробелы, дефис или запятую")
        return

    await create_or_update_profile(user_id, {
        UserProfileFields.AREA.value: text,
        UserProfileFields.CURRENT_STEP.value: 1
    })

    await clear_messages(user_id, global_msg_contacted_fast, global_msg_fast)
    await clear_waiting_input(state, message.chat.id, user_id)

    msg = await message.answer(
        text=f"✅ Записал!\n\nТеперь укажите краткое название вашей деятельности (например: Фитнес-тренер, Веб-дизайнер, Продажа нижнего белья, Массажист и тп ) — это то, что пользователи увидят в списке при поиске.",
        reply_markup=get_product_name_keyboard()
    )
    add_message(global_msg_contacted_fast, user_id, msg)


async def extract_and_save_profession(message, state, user_id):
    text = (message.text or "").strip()
    if await check_cancel_input(text, message, state): return

    if not (2 <= len(text) <= 50):
        await send_error(message, user_id, "Ошибка: название деятельности должно быть от 2 до 50 символов")
        return

    await create_or_update_profile(user_id, {
        UserProfileFields.PROFESSION.value: text,
        UserProfileFields.CURRENT_STEP.value: 2
    })

    await clear_messages(user_id, global_msg_contacted_fast, global_msg_fast)
    await clear_waiting_input(state, message.chat.id, user_id)

    msg = await message.answer(
        text=f"✅ Записал: {text}!\n\nТеперь расскажи о себе и своей деятельности (от 50 до 300 символов) — эту информацию увидят другие участники клуба, так что постарайся описать всё понятно и привлекательно 😊",
        reply_markup=get_product_desc_keyboard()
    )
    add_message(global_msg_contacted_fast, user_id, msg)


async def extract_and_save_description(message, state, user_id):
    text = (message.text or "").strip()
    if await check_cancel_input(text, message, state): return
    
    if not (50 <= len(text) <= 300):
        await send_error(message, user_id, f"Ошибка: описание должно быть от 50 до 300 символов (сейчас {len(text)})")
        return

    # Валидация на Эмодзи удалена по просьбе пользователя
    
    await create_or_update_profile(user_id, {
        UserProfileFields.DESCRIPTION_PROFESSION.value: text,
        UserProfileFields.CURRENT_STEP.value: 3
    })

    await clear_messages(user_id, global_msg_contacted_fast, global_msg_fast)
    await clear_waiting_input(state, message.chat.id, user_id)

    from services.keyboards.keyboards_for_registration import get_add_service_keyboard
    msg = await message.answer(
        text=f"✅ Описание сохранено!\n\nТеперь давайте добавим ваши услуги. Нажмите кнопку ниже, чтобы описать первую услугу.",
        reply_markup=get_add_service_keyboard(is_first=True)
    )
    add_message(global_msg_contacted_fast, user_id, msg)

async def extract_and_save_service_name(message, state, user_id):
    text = (message.text or "").strip()
    if await check_cancel_input(text, message, state): return

    if not (2 <= len(text) <= 50):
        await send_error(message, user_id, "Ошибка: название услуги должно быть от 2 до 50 символов")
        return

    profile = get_profile(user_id) or {}
    temp_service = profile.get(UserProfileFields.TEMP_SERVICE.value, {})
    temp_service['name'] = text

    await create_or_update_profile(user_id, {
        UserProfileFields.TEMP_SERVICE.value: temp_service
    })

    await clear_messages(user_id, global_msg_contacted_fast, global_msg_fast)
    await clear_waiting_input(state, message.chat.id, user_id)

    from services.keyboards.keyboards_for_registration import get_add_info_product_keyboard
    msg = await message.answer(
        text=(
            f"✅ Отлично! Услуга: {text}\n\n"
            "Теперь подробно, но кратко опишите детали услуги (что входит, нюансы). "
            "Также укажите условия отмены — за какое время вы готовы принять отмену без последствий (например: за час, за день, за неделю).\n\n"
            "⚠️ Пожалуйста, не пишите в этом разделе цену — для неё будет отдельный шаг."
        ),
        reply_markup=get_add_info_product_keyboard()
    )
    add_message(global_msg_contacted_fast, user_id, msg)

async def extract_and_save_service_desc(message, state, user_id):
    text = (message.text or "").strip()
    if await check_cancel_input(text, message, state): return

    if not (50 <= len(text) <= 300):
        await send_error(message, user_id, f"Ошибка: описание услуги должно быть от 50 до 300 символов (сейчас {len(text)})")
        return

    profile = get_profile(user_id) or {}
    temp_service = profile.get(UserProfileFields.TEMP_SERVICE.value, {})
    temp_service['description'] = text

    await create_or_update_profile(user_id, {
        UserProfileFields.TEMP_SERVICE.value: temp_service
    })

    await clear_messages(user_id, global_msg_contacted_fast, global_msg_fast)
    await clear_waiting_input(state, message.chat.id, user_id)

    msg = await message.answer(
        text=f"✅ Описание добавлено!\n\nУкажите прайс в долларах целым числом (от 1 до 1000) — 1$ = 1 монета клуба 🪙\n\nЦену здесь лучше поставить такую же, как вне клуба, или чуть ниже — но не выше 😊",
        reply_markup=get_price_keyboard()
    )
    add_message(global_msg_contacted_fast, user_id, msg)

async def extract_and_save_price(message, state, user_id):
    text = (message.text or "").strip()
    if await check_cancel_input(text, message, state): return

    if not text.isdigit():
        await send_error(message, user_id, "Ошибка: цена должна быть целым числом")
        return
        
    price_val = int(text)
    if not (1 <= price_val <= 1000):
        await send_error(message, user_id, "Ошибка: цена услуги должна быть от 1 до 1000 монет")
        return

    profile = get_profile(user_id) or {}
    temp_service = profile.get(UserProfileFields.TEMP_SERVICE.value, {})
    temp_service['price'] = text
    
    services = profile.get(UserProfileFields.SERVICES.value, [])
    services.append(temp_service)

    await create_or_update_profile(user_id, {
        UserProfileFields.SERVICES.value: services,
        UserProfileFields.TEMP_SERVICE.value: {},
        UserProfileFields.CURRENT_STEP.value: 4
    })

    await clear_messages(user_id, global_msg_contacted_fast, global_msg_fast)
    await clear_waiting_input(state, message.chat.id, user_id)

    from services.keyboards.keyboards_for_registration import get_add_service_keyboard
    msg = await message.answer(
        text=f"✅ Услуга сохранена!\n\nВы можете добавить еще одну услугу или перейти к завершению регистрации.",
        reply_markup=get_add_service_keyboard(is_first=False)
    )
    add_message(global_msg_contacted_fast, user_id, msg)

async def extract_and_save_socials(message, state, user_id):
    text = (message.text or "").strip()
    if await check_cancel_input(text, message, state): return

    clean_text = text.replace(',', ' ').replace('\n', ' ')
    links = [link.strip() for link in clean_text.split() if link.strip()]

    if not (1 <= len(links) <= 10):
        await send_error(message, user_id, f"Ошибка: укажите от 1 до 10 ссылок (вы указали {len(links)})")
        return

    await create_or_update_profile(user_id, {
        UserProfileFields.SOCIAL_LINKS.value: links,
        UserProfileFields.CURRENT_STEP.value: 5
    })

    await clear_messages(user_id, global_msg_contacted_fast, global_msg_fast)
    await clear_waiting_input(state, message.chat.id, user_id)

    profile = get_profile(user_id) or {}
    required_fields = [
        UserProfileFields.AREA.value,
        UserProfileFields.SERVICES.value,
        UserProfileFields.DESCRIPTION_PROFESSION.value,
        UserProfileFields.SOCIAL_LINKS.value,
        UserProfileFields.NAME.value
    ]
    
    is_valid = all(profile.get(field) for field in required_fields) and len(profile.get(UserProfileFields.SERVICES.value, [])) > 0

    if is_valid:
        msg = await message.answer(
            text="✅ Прекрасно - анкета заполнена!",
            reply_markup=get_final_profile_keyboard()
        )
    else:
        msg = await message.answer(
            text="⚠️ Упс, что-то пошло не так. Некоторые поля отсутствуют. Пожалуйста, начните заполнение анкеты заново.",
            reply_markup=get_full_name_keyboard() 
        )
    add_message(global_msg_contacted_fast, user_id, msg)