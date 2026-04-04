from __future__ import annotations

import json
import copy
from filelock import FileLock

from filesManagers.maker_dirs import ensure_file_exists
from initApp.config_loader import config
from services.users_utils.user_profile_manager import load_profiles, get_profile, ALL_PROFILES_LIST, save_profiles

"""
Менеджер временных профилей для безопасного редактирования.

Структура записи в temp_profiles.json для одного user_id:
{
    "editing": {...}       — профиль в процессе редактирования (until FINISH_EDITING)
    "new": {...}           — новый профиль после FINISH_EDITING (pending moderation)
    "old": {...}           — snapshot старого профиля до изменений (для отката при REJECT)
}

Фазы:
1. CONFIRM_EDIT_PROFILE   → copy_profile_to_temp()  → запись в "editing"
2. изменения полей        → update_temp_profile()   → обновление "editing"
3. FINISH_EDITING         → freeze_temp_profile()   → "editing" → "new", "old" = текущий основной
4. ACCEPT_CHANGES         → apply_new_profile()     → "new" → основной файл, удалить запись
5. REJECT_CHANGES         → apply_old_profile()     → "old" → основной (если надо rollback), удалить запись
"""

# Ключи внутри записи temp
_KEY_EDITING = "editing"
_KEY_NEW = "new"
_KEY_OLD = "old"


def _load_temp_profiles() -> dict[int, dict]:
    """Загрузка временных профилей из файла."""
    ensure_file_exists(config.TEMP_PROFILE_PATH)
    try:
        with open(config.TEMP_PROFILE_PATH, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return {}
            return {int(uid): data for uid, data in json.loads(content).items()}
    except (json.JSONDecodeError, FileNotFoundError):
        return {}


def _save_temp_profiles(profiles: dict[int, dict]):
    """Сохранение временных профилей в файл."""
    ensure_file_exists(config.TEMP_PROFILE_PATH)
    with open(config.TEMP_PROFILE_PATH, "w", encoding="utf-8") as f:
        json.dump(
            {str(uid): data for uid, data in profiles.items()},
            f,
            ensure_ascii=False,
            indent=2
        )


# ─── Фаза 1: вход в редактирование ────────────────────────────────────────────

def copy_profile_to_temp(user_id: int) -> bool:
    """Копирует текущий профиль во временный файл (фаза 'editing')."""
    lock_path = f"{config.TEMP_PROFILE_PATH}.lock"
    with FileLock(lock_path, timeout=10):
        profile = get_profile(user_id)
        if not profile:
            return False
        temp_profiles = _load_temp_profiles()
        temp_profiles[user_id] = {_KEY_EDITING: copy.deepcopy(profile)}
        _save_temp_profiles(temp_profiles)
        return True


# ─── Фаза 2: обновление полей при редактировании ──────────────────────────────

def get_temp_profile(user_id: int) -> dict | None:
    """Возвращает профиль в стадии editing."""
    temp_profiles = _load_temp_profiles()
    record = temp_profiles.get(user_id)
    if not record:
        return None
    return record.get(_KEY_EDITING)


def update_temp_profile(user_id: int, updates: dict) -> bool:
    """Обновляет поля в editing-профиле."""
    lock_path = f"{config.TEMP_PROFILE_PATH}.lock"
    with FileLock(lock_path, timeout=10):
        temp_profiles = _load_temp_profiles()
        record = temp_profiles.get(user_id)
        if not record or _KEY_EDITING not in record:
            return False
        for key, value in updates.items():
            record[_KEY_EDITING][key] = value
        _save_temp_profiles(temp_profiles)
        return True


# ─── Фаза 3: завершение редактирования (freeze) ───────────────────────────────

def freeze_temp_profile(user_id: int) -> bool:
    """
    Переводит editing в new, сохраняет old (текущий основной).
    После этого данные готовы к проверке модератором.
    editing-профиль удаляется.
    """
    lock_path = f"{config.TEMP_PROFILE_PATH}.lock"
    with FileLock(lock_path, timeout=10):
        temp_profiles = _load_temp_profiles()
        record = temp_profiles.get(user_id)
        if not record or _KEY_EDITING not in record:
            return False

        original = get_profile(user_id)
        if not original:
            return False

        new_record = {
            _KEY_NEW: copy.deepcopy(record[_KEY_EDITING]),
            _KEY_OLD: copy.deepcopy(original),
        }
        temp_profiles[user_id] = new_record
        _save_temp_profiles(temp_profiles)
        return True


def get_new_profile(user_id: int) -> dict | None:
    """Возвращает новый (ожидающий подтверждения) профиль."""
    temp_profiles = _load_temp_profiles()
    record = temp_profiles.get(user_id)
    if not record:
        return None
    return record.get(_KEY_NEW)


def get_old_profile(user_id: int) -> dict | None:
    """Возвращает старый (snapshot до изменений) профиль."""
    temp_profiles = _load_temp_profiles()
    record = temp_profiles.get(user_id)
    if not record:
        return None
    return record.get(_KEY_OLD)


# ─── Фаза 4: принятие модератором ─────────────────────────────────────────────

def apply_new_profile(user_id: int) -> bool:
    """Применяет 'new' профиль в основной файл (вызывается при ACCEPT)."""
    lock_path = f"{config.TEMP_PROFILE_PATH}.lock"
    with FileLock(lock_path, timeout=10):
        temp_profiles = _load_temp_profiles()
        record = temp_profiles.get(user_id)
        if not record or _KEY_NEW not in record:
            return False

        profiles = load_profiles()
        profiles[user_id] = copy.deepcopy(record[_KEY_NEW])
        ALL_PROFILES_LIST.clear()
        ALL_PROFILES_LIST.update(profiles)
        save_profiles()

        del temp_profiles[user_id]
        _save_temp_profiles(temp_profiles)
        return True


# ─── Фаза 5: отклонение модератором ───────────────────────────────────────────

def apply_old_profile(user_id: int) -> bool:
    """
    Откатывает профиль к 'old' (вызывается при REJECT если надо revert).
    В нашем случае основной файл ещё не был изменён — просто удаляем запись.
    """
    lock_path = f"{config.TEMP_PROFILE_PATH}.lock"
    with FileLock(lock_path, timeout=10):
        temp_profiles = _load_temp_profiles()
        if user_id in temp_profiles:
            del temp_profiles[user_id]
            _save_temp_profiles(temp_profiles)
        return True


# ─── Удаление записи ──────────────────────────────────────────────────────────

def delete_temp_profile(user_id: int) -> bool:
    """Удаляет любую временную запись профиля пользователя."""
    lock_path = f"{config.TEMP_PROFILE_PATH}.lock"
    with FileLock(lock_path, timeout=10):
        temp_profiles = _load_temp_profiles()
        if user_id in temp_profiles:
            del temp_profiles[user_id]
            _save_temp_profiles(temp_profiles)
            return True
        return False


# ─── Сравнение ────────────────────────────────────────────────────────────────

def has_profile_changes(user_id: int) -> bool:
    """
    Сравнивает editing-профиль с оригинальным.
    Возвращает True если хотя бы одно значимое поле изменено.
    """
    from entity.Enums_entity import UserProfileFields

    original = get_profile(user_id)
    temp = get_temp_profile(user_id)

    if not original or not temp:
        return False

    fields_to_compare = [
        UserProfileFields.NAME.value,
        UserProfileFields.AREA.value,
        UserProfileFields.PROFESSION.value,
        UserProfileFields.DESCRIPTION_PROFESSION.value,
        UserProfileFields.SOCIAL_LINKS.value,
        UserProfileFields.SERVICES.value,
    ]

    for field in fields_to_compare:
        orig_val = original.get(field)
        temp_val = temp.get(field)
        if orig_val != temp_val:
            return True

    return False


def build_diff_text(user_id: int) -> str:
    """
    Строит текст diff между old и new профилями для отображения модератору.
    Показывает только изменённые поля.
    """
    from entity.Enums_entity import UserProfileFields
    import html as html_module

    old = get_old_profile(user_id) or {}
    new = get_new_profile(user_id) or {}

    field_labels = {
        UserProfileFields.NAME.value: "ФИО",
        UserProfileFields.AREA.value: "Район",
        UserProfileFields.PROFESSION.value: "Деятельность",
        UserProfileFields.DESCRIPTION_PROFESSION.value: "О себе",
        UserProfileFields.SOCIAL_LINKS.value: "Ссылки/соцсети",
        UserProfileFields.SERVICES.value: "Услуги",
    }

    lines = []
    for field, label in field_labels.items():
        old_val = old.get(field)
        new_val = new.get(field)
        if old_val == new_val:
            continue
        if field == UserProfileFields.SERVICES.value:
            lines.append(f"\n📌 <b>{label}:</b>")
            old_services = old_val or []
            new_services = new_val or []
            for i, svc in enumerate(new_services, 1):
                svc_name = html_module.escape(str(svc.get("name", "")))
                svc_desc = html_module.escape(str(svc.get("description", "")))
                svc_price = html_module.escape(str(svc.get("price", "")))
                lines.append(f"   {i}. <b>{svc_name}</b>\n      {svc_desc}\n      💰 {svc_price}")
            if old_services:
                lines.append(f"   <i>(было {len(old_services)} услуг, стало {len(new_services)})</i>")
        elif field == UserProfileFields.SOCIAL_LINKS.value:
            old_links = "\n".join(old_val or []) or "—"
            new_links = "\n".join(new_val or []) or "—"
            lines.append(
                f"\n📌 <b>{label}:</b>\n"
                f"   было: <i>{html_module.escape(str(old_links))}</i>\n"
                f"   стало: <b>{html_module.escape(str(new_links))}</b>"
            )
        else:
            lines.append(
                f"\n📌 <b>{label}:</b>\n"
                f"   было: <i>{html_module.escape(str(old_val or '—'))}</i>\n"
                f"   стало: <b>{html_module.escape(str(new_val or '—'))}</b>"
            )

    return "\n".join(lines) if lines else "(нет изменений)"
