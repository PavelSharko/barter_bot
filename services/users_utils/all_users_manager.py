from __future__ import annotations

import json
from datetime import datetime

from filelock import FileLock

from filesManagers.maker_dirs import ensure_file_exists
from initApp.config_loader import config
from entity.Enums_entity import (
    UserFields,
    UserFlags,
    UserMetrics,
    UserLifecycleStatus,
    ReviewStatus,
    ProfileStatus,
    UserCategory,
    Sity
)

# Глобальный кэш пользователей
ALL_USERS_LIST: dict[int, dict] = {}

"""
Менеджер пользователей — хранение, регистрация и управление данными пользователей бота.

Смысл файла:
- Централизованно управляет всей внутренней базой пользователей проекта в формате JSON.
- Реализует базовые CRUD-операции (создание, чтение, обновление, удаление) над данными пользователей в безопасном и многопоточном режиме.
- Использует файловые блокировки через FileLock для предотвращения конфликтов при одновременной записи.
- Все операции с файлом данных предполагают автоматическое создание файла при отсутствии и контроль консистентности через глобальный кэш.
- Поддерживает автоматическую регистрацию новых пользователей с сохранением основных данных: имя, дата регистрации, телефон и прочее.
- Предлагает быстрый доступ к имени пользователя, его профилю и историю заказов.
- Для расширения: структура легко дополняется новыми полями или функциями, связанные с профилем пользователя.

**Задача менеджера**: гарантировать надёжное и удобное хранение всех данных пользователей в целом проекте,
быстро выполнять массовые действия и одновременно предотвращать ошибки параллельного доступа.
"""



def load_all_users() -> dict[int, dict]:
    """Чтение пользователей (без лока)."""
    global ALL_USERS_LIST
    ensure_file_exists(config.ALL_USERS_PATH)
    try:
        with open(config.ALL_USERS_PATH, "r", encoding="utf-8") as f:
            ALL_USERS_LIST = {int(uid): data for uid, data in json.load(f).items()}
    except (json.JSONDecodeError, FileNotFoundError):
        ALL_USERS_LIST = {}
    return dict(ALL_USERS_LIST)


def save_all_users():
    """Запись пользователей (без лока — контроль снаружи)."""
    ensure_file_exists(config.ALL_USERS_PATH)
    with open(config.ALL_USERS_PATH, "w", encoding="utf-8") as f:
        json.dump(
            {str(uid): data for uid, data in ALL_USERS_LIST.items()},
            f,
            ensure_ascii=False,
            indent=2
        )


async def format_user_name(bot, user_id: int) -> str:
    """Определяет имя пользователя: @username или 'Имя Фамилия'."""
    try:
        user = await bot.get_chat(user_id)
        if getattr(user, "username", None):
            return f"@{user.username}"
        elif getattr(user, "first_name", None) or getattr(user, "last_name", None):
            return " ".join(filter(None, [user.first_name, user.last_name])).strip()
        else:
            return f"ID{user_id}"
    except Exception:
        return f"ID{user_id}"


async def register_and_check_user(user_id: int, bot=None) -> bool:
    """Регистрирует нового пользователя, если его нет."""
    lock_path = f"{config.ALL_USERS_PATH}.lock"

    with FileLock(lock_path, timeout=10):  # Лок на всё чтение + запись
        users = load_all_users()  # читаем актуальные данные под локом
        if user_id not in users:
            user_name = None
            if bot is not None:
                user_name = await format_user_name(bot, user_id)

            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            users[user_id] = {
                UserFields.NAME_TG.value: user_name or f"ID{user_id}",
                UserFields.NAME_REAL.value: None,
                UserFields.DATE_REG.value: current_time,
                UserFields.PHONE.value: None,
                UserFields.UPDATED_AT.value: current_time,
                UserFlags.RULES_READ.value: False,
                UserFlags.IS_EXCLUDED.value: False,
                UserFields.REGION.value: Sity.BALI.value,
                UserMetrics.BALANCE.value: 0,
                UserMetrics.TOTAL_DEALS_COUNT.value: 0,
                UserMetrics.RATING_SUM.value: 0,
                UserMetrics.RATING_AVG.value: 0.0,
                UserFields.RULES_REMINDER_SENT_AT.value: None,
                UserFields.STATUS.value: UserLifecycleStatus.CONTACTED.value,
                UserFields.FORGOT_REVIEW_STATUS.value: ReviewStatus.NONE.value,
                UserFields.PROFILE_STATUS.value: ProfileStatus.EMPTY.value,
                UserFields.CATEGORY.value: None,  # null по умолчанию
            }

            # обновляем глобальный кеш
            ALL_USERS_LIST.clear()
            ALL_USERS_LIST.update(users)

            save_all_users()
            return True

    return False


def get_user_name(user_id: int) -> str | None:
    """Возвращает сохранённое имя пользователя."""
    users = load_all_users()
    user = users.get(user_id)
    return user.get(UserFields.NAME_TG.value) if user else None


def get_all_users() -> dict[int, dict]:
    """Возвращает всех пользователей."""
    return load_all_users()


def remove_user(user_id: int) -> bool:
    """Удаляет пользователя."""
    load_all_users()
    if user_id in ALL_USERS_LIST:
        del ALL_USERS_LIST[user_id]
        save_all_users()
        return True
    return False


def update_user_field(user_id: int, field: str, value) -> bool:
    """Обновляет поле field у пользователя."""
    load_all_users()
    if user_id not in ALL_USERS_LIST:
        return False
    ALL_USERS_LIST[user_id][field] = value
    save_all_users()
    return True