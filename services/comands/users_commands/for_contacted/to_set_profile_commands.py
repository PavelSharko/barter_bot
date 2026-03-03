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

    # Только буквы, пробелы, дефисы
    if not re.match(r"^[a-zA-Zа-яА-ЯёЁ\s\-]+$", text):
        await send_error(message, user_id, "Ошибка: район должен содержать только буквы, пробелы и дефис")
        return

    await create_or_update_profile(user_id, {
        UserProfileFields.AREA.value: text,
        UserProfileFields.CURRENT_STEP.value: 1
    })

    await clear_messages(user_id, global_msg_contacted_fast, global_msg_fast)
    await clear_waiting_input(state, message.chat.id, user_id)

    msg = await message.answer(
        text=f"✅ Записал!\n\nТеперь скажи — как называется твоя услуга или товар?",
        reply_markup=get_product_name_keyboard()
    )
    add_message(global_msg_contacted_fast, user_id, msg)


async def extract_and_save_product_name(message, state, user_id):
    text = (message.text or "").strip()
    if await check_cancel_input(text, message, state): return

    # Валидация Услуги
    # Длина 3-30
    if not (3 <= len(text) <= 30):
        await send_error(message, user_id, "Ошибка: название услуги должно быть от 3 до 30 символов")
        return

    # Только буквы, пробелы, дефисы, точки, слеши
    if not re.match(r"^[a-zA-Zа-яА-ЯёЁ\s\-\./]+$", text):
        await send_error(message, user_id, "Ошибка: недопустимые символы в названии услуги")
        return

    await create_or_update_profile(user_id, {
        UserProfileFields.SERVICE_NAME.value: text,
        UserProfileFields.CURRENT_STEP.value: 2
    })

    await clear_messages(user_id, global_msg_contacted_fast, global_msg_fast)
    await clear_waiting_input(state, message.chat.id, user_id)

    msg = await message.answer(
        text=f"✅ Принято!\n\nТеперь расскажи о своей услуге или товаре (от 100 до 500 символов) — эту информацию увидят другие участники клуба, так что постарайся описать всё понятно и привлекательно 😊\n\nТакже укажи условия отмены — за какое время ты готов принять отмену без последствий (например: за час, за день, за неделю):",
        reply_markup=get_product_desc_keyboard()
    )
    add_message(global_msg_contacted_fast, user_id, msg)


async def extract_and_save_description(message, state, user_id):
    text = (message.text or "").strip()
    if await check_cancel_input(text, message, state): return
    
    # Валидация Описания
    # Длина 100-500 (строго)
    if not (100 <= len(text) <= 500):
        await send_error(message, user_id, f"Ошибка: описание должно быть от 100 до 500 символов (сейчас {len(text)})")
        return

    # Любые символы кроме эмодзи (простая проверка на диапазон, не идеальная, но рабочая для большинства)
    # Диапазон эмодзи в Unicode основной: U+1F600-U+1F64F и другие блоки.
    # Проще проверить, что есть буквы. 
    # Но требование "Любые символы кроме только эмодзи" может значить "не должно состоять ТОЛЬКО из эмодзи".
    # Но обычно просят "без эмодзи". Поставлю проверку на наличие эмодзи в тексте.
    # Если найдем эмодзи - ошибка.
    # Базовый паттерн для эмодзи (не полный, но покроет основные):
    if re.search(r"[\U00010000-\U0010ffff]", text): # Широкий диапазон 4-байтовых символов, куда попадают эмодзи
         await send_error(message, user_id, "Ошибка: использование эмодзи в описании запрещено")
         return

    await create_or_update_profile(user_id, {
        UserProfileFields.SERVICE_DESCRIPTION.value: text,
        UserProfileFields.CURRENT_STEP.value: 3
    })

    await clear_messages(user_id, global_msg_contacted_fast, global_msg_fast)
    await clear_waiting_input(state, message.chat.id, user_id)

    msg = await message.answer(
        text=f"✅ Описание сохранено!\n\nУкажи прайс в долларах целым числом — 1$ = 1 монета клуба 🪙\n\nКстати, цену здесь лучше поставить такую же, как вне клуба, или чуть ниже — но не выше 😊\n\nЦена будет проверена модератором при одобрении анкеты.",
        reply_markup=get_price_keyboard()
    )
    add_message(global_msg_contacted_fast, user_id, msg)


async def extract_and_save_price(message, state, user_id):
    text = (message.text or "").strip()
    if await check_cancel_input(text, message, state): return

    # Валидация Прайса
    # Должно быть число от 1 до 99
    if not text.isdigit():
        await send_error(message, user_id, "Ошибка: цена должна быть целым числом")
        return
        
    price_val = int(text)
    if not (1 <= price_val <= 99):
        await send_error(message, user_id, "Ошибка: цена должна быть от 1 до 99")
        return

    await create_or_update_profile(user_id, {
        UserProfileFields.PRICE_INFO.value: text,
        UserProfileFields.CURRENT_STEP.value: 4
    })

    await clear_messages(user_id, global_msg_contacted_fast, global_msg_fast)
    await clear_waiting_input(state, message.chat.id, user_id)

    msg = await message.answer(
        text=f"✅ Цена записана!\n\nПоследний шаг — скинь ссылки на соцсети или отзывы (Instagram, Telegram и т.д.):",
        reply_markup=get_socials_keyboard()
    )
    add_message(global_msg_contacted_fast, user_id, msg)


async def extract_and_save_socials(message, state, user_id):
    text = (message.text or "").strip()
    if await check_cancel_input(text, message, state): return

    # Валидация Соцсетей
    # Разделитель: пробел, запятая или перенос строки
    # Заменяем запятые и переносы на пробелы, потом сплитим
    clean_text = text.replace(',', ' ').replace('\n', ' ')
    links = [link.strip() for link in clean_text.split() if link.strip()]

    # Минимум 1, максимум 10
    if not (1 <= len(links) <= 10):
        await send_error(message, user_id, f"Ошибка: укажите от 1 до 10 ссылок (вы указали {len(links)})")
        return

    await create_or_update_profile(user_id, {
        UserProfileFields.SOCIAL_LINKS.value: links,
        UserProfileFields.CURRENT_STEP.value: 5
    })

    await clear_messages(user_id, global_msg_contacted_fast, global_msg_fast)
    await clear_waiting_input(state, message.chat.id, user_id)

    # Валидация всех полей (финальная проверка, хотя мы уже провалидировали каждый шаг)
    profile = get_profile(user_id) or {}
    required_fields = [
        UserProfileFields.AREA.value,
        UserProfileFields.SERVICE_NAME.value,
        UserProfileFields.SERVICE_DESCRIPTION.value,
        UserProfileFields.PRICE_INFO.value,
        UserProfileFields.SOCIAL_LINKS.value,
        UserProfileFields.NAME.value
    ]
    
    is_valid = all(profile.get(field) for field in required_fields)

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