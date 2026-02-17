from __future__ import annotations

import json
from datetime import datetime
from filelock import FileLock

from filesManagers.maker_dirs import ensure_file_exists
from initApp.config_loader import config
from entity.Enums_entity import UserProfileFields

# Глобальный кэш профилей
ALL_PROFILES_LIST: dict[int, dict] = {}

"""
Менеджер профилей пользователей — хранение дополнительных данных анкеты.
"""

def load_profiles() -> dict[int, dict]:
    """Чтение профилей (без лока)."""
    global ALL_PROFILES_LIST
    ensure_file_exists(config.USER_PROFILE_PATH)
    try:
        with open(config.USER_PROFILE_PATH, "r", encoding="utf-8") as f:
            ALL_PROFILES_LIST = {int(uid): data for uid, data in json.load(f).items()}
    except (json.JSONDecodeError, FileNotFoundError):
        ALL_PROFILES_LIST = {}
    return dict(ALL_PROFILES_LIST)


def save_profiles():
    """Запись профилей (без лока — контроль снаружи)."""
    ensure_file_exists(config.USER_PROFILE_PATH)
    with open(config.USER_PROFILE_PATH, "w", encoding="utf-8") as f:
        json.dump(
            {str(uid): data for uid, data in ALL_PROFILES_LIST.items()},
            f,
            ensure_ascii=False,
            indent=2
        )


def get_profile(user_id: int) -> dict | None:
    """Возвращает профиль пользователя из кэша (или подгружает)."""
    # Если кэш пуст, попробуем загрузить (хотя лучше полагаться на внешний load)
    if not ALL_PROFILES_LIST:
        load_profiles()
    return ALL_PROFILES_LIST.get(user_id)


async def create_or_update_profile(user_id: int, updates: dict) -> bool:
    """
    Создает или обновляет профиль пользователя.
    Автоматически обновляет updated_at и version.
    """
    lock_path = f"{config.USER_PROFILE_PATH}.lock"

    with FileLock(lock_path, timeout=10):
        profiles = load_profiles()
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if user_id not in profiles:
            # Создание нового профиля
            profiles[user_id] = {
                UserProfileFields.AREA.value: None,
                UserProfileFields.SERVICE_NAME.value: None,
                UserProfileFields.SERVICE_DESCRIPTION.value: None,
                UserProfileFields.PRICE_INFO.value: None,
                UserProfileFields.SOCIAL_LINKS.value: [],
                UserProfileFields.CURRENT_STEP.value: 0,
                UserProfileFields.CREATED_AT.value: current_time,
                UserProfileFields.UPDATED_AT.value: current_time,
                UserProfileFields.VERSION.value: 1
            }
        
        # Обновление полей
        profile = profiles[user_id]
        
        # Применяем обновления
        for key, value in updates.items():
            profile[key] = value
            
        # Системные обновления
        profile[UserProfileFields.UPDATED_AT.value] = current_time
        # Увеличиваем версию только если создавался не сейчас (хотя можно и просто инкремент)
        if UserProfileFields.VERSION.value in profile:
             profile[UserProfileFields.VERSION.value] += 1
        else:
             profile[UserProfileFields.VERSION.value] = 1

        # Обновляем кэш и сохраняем
        ALL_PROFILES_LIST.clear()
        ALL_PROFILES_LIST.update(profiles)
        save_profiles()
        return True


def is_profile_completed(user_id: int) -> bool:
    """
    Проверяет, что все обязательные поля анкеты заполнены.
    """
    profile = get_profile(user_id)
    if not profile:
        return False
        
    required_fields = [
        UserProfileFields.NAME.value,
        UserProfileFields.AREA.value,
        UserProfileFields.SERVICE_NAME.value,
        UserProfileFields.SERVICE_DESCRIPTION.value,
        UserProfileFields.PRICE_INFO.value,
        UserProfileFields.SOCIAL_LINKS.value
    ]
    
    for field in required_fields:
        value = profile.get(field)
        if not value: # Проверка на None или пустую строку/список
            return False
        if isinstance(value, list) and len(value) == 0: # Доп. проверка для списка
            return False
            
    return True
