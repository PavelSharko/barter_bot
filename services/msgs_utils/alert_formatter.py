# services/msgs_utils/alert_formatter.py
import html
from entity.Enums_entity import UserFields, UserProfileFields

def _get_user_display_name(user_id, users_db, profiles_db) -> str:
    """
    Вспомогательный метод для построения красивого имени: Имя_реальное (@юзернейм) (ID: XXX)
    Абсолютно устойчив к типам ключей (int/str).
    """
    uid_str = str(user_id)
    uid_int = int(user_id) if uid_str.isdigit() else user_id

    # Ищем данные пользователя
    u_data = users_db.get(uid_int) or users_db.get(uid_str) or {}
    p_data = profiles_db.get(uid_str) or profiles_db.get(uid_int) or {}

    tg_name = u_data.get(UserFields.NAME_TG.value) or f"ID {user_id}"
    if tg_name != f"ID {user_id}" and not tg_name.startswith("@"):
        tg_name = f"@{tg_name}"

    real_name = p_data.get(UserProfileFields.NAME.value) or u_data.get(UserFields.NAME_REAL.value)
    
    return f"{real_name} ({tg_name})" if real_name else tg_name

def format_new_deal_alert(deal_id: str, client_id, provider_id, service_name: str, price: float, users_db: dict, profiles_db: dict) -> str:
    """Форматирует алерт создания новой сделки для модератора."""
    c_display = _get_user_display_name(client_id, users_db, profiles_db)
    p_display = _get_user_display_name(provider_id, users_db, profiles_db)

    return (
        f"⚠️ <b>Создана новая сделка</b> ⚠️\n"
        f"ID Сделки: <code>{deal_id}</code>\n"
        f"👤 <b>Заказчик:</b> {html.escape(c_display)} (ID: <code>{client_id}</code>)\n"
        f"🛠 <b>Исполнитель:</b> {html.escape(p_display)} (ID: <code>{provider_id}</code>)\n"
        f"📦 <b>Услуга:</b> {html.escape(str(service_name))}\n"
        f"💰 <b>Сумма:</b> {price:g} монет."
    )

def format_deal_completed_alert(deal_id: str, client_id, provider_id, service_name: str, server_commission: float, users_db: dict, profiles_db: dict) -> str:
    """Форматирует алерт успешного завершения сделки для модератора."""
    c_display = _get_user_display_name(client_id, users_db, profiles_db)
    p_display = _get_user_display_name(provider_id, users_db, profiles_db)

    return (
        f"✅ <b>Сделка завершена</b> ✅\n"
        f"ID Сделки: <code>{deal_id}</code>\n"
        f"👤 <b>Заказчик:</b> {html.escape(c_display)} (ID: <code>{client_id}</code>)\n"
        f"🛠 <b>Исполнитель:</b> {html.escape(p_display)} (ID: <code>{provider_id}</code>)\n"
        f"📦 <b>Услуга:</b> {html.escape(str(service_name))}\n"
        f"💰 <b>Комиссия модератора:</b> +<b>{server_commission:g}</b> 🪙 (зачислена на ваш баланс)."
    )

def format_deal_blocked_alert(client_id, provider_id, users_db: dict, profiles_db: dict) -> str:
    """Форматирует алерт при попытке заказать услугу у заблокированного/находящегося на модерации исполнителя."""
    c_display = _get_user_display_name(client_id, users_db, profiles_db)
    p_display = _get_user_display_name(provider_id, users_db, profiles_db)

    return (
        f"⚠️ <b>Попытка начать сделку (Отказ)</b> ⚠️\n"
        f"👤 <b>Заказчик:</b> {html.escape(c_display)} (ID: <code>{client_id}</code>)\n"
        f"🛠 <b>Исполнитель:</b> {html.escape(p_display)} (ID: <code>{provider_id}</code>)\n\n"
        f"<i>Заказчик пытался создать сделку, но анкета исполнителя еще находится на модерации после правок. Проверьте заявки!</i>"
    )

def format_profile_changed_alert(user_id, username: str, diff_text: str, users_db: dict, profiles_db: dict) -> str:
    """Форматирует алерт об изменении профиля клиента."""
    u_display = _get_user_display_name(user_id, users_db, profiles_db)
    username_str = f"@{username.lstrip('@')}" if username else "Не указан"

    return (
        f"⚠️ <b>Клиент хочет изменить профиль!</b>\n"
        f"👤 <b>Пользователь:</b> {html.escape(u_display)} (ID: <code>{user_id}</code>)\n"
        f"Username: <code>{html.escape(username_str)}</code>\n\n"
        f"<b>Изменённые поля:</b>\n"
        f"{diff_text}"
    )

def format_new_registration_alert(user_id, username: str, name: str, area: str, profession: str, desc_prof: str, links: str, services_list: list, users_db: dict, profiles_db: dict) -> str:
    """Форматирует алерт о новой заявке на регистрацию."""
    u_display = _get_user_display_name(user_id, users_db, profiles_db)
    username_str = f"@{str(username).lstrip('@')}" if username else "Не указан"

    text = (
        f"🆕 <b>Новая заявка на вступление!</b>\n"
        f"👤 <b>Пользователь:</b> {html.escape(str(u_display))} (ID: <code>{user_id}</code>)\n"
        f"Username: <code>{html.escape(str(username_str))}</code>\n\n"
        f"<b>ФИО</b>: {html.escape(str(name or 'Не указано'))}\n"
        f"<b>Район</b>: {html.escape(str(area or 'Не указан'))}\n"
        f"<b>Деятельность</b>: {html.escape(str(profession or 'Не указана'))}\n"
        f"<b>О себе</b>: {html.escape(str(desc_prof or 'Не указано'))}\n"
        f"<b>Ссылки</b>: \n{html.escape(str(links or 'Не указаны'))}\n\n"
    )

    if services_list and isinstance(services_list, list):
        text += "<b>Услуги:</b>\n"
        for i, s in enumerate(services_list, 1):
            if isinstance(s, dict):
                s_name = s.get('name') or "Без названия"
                s_desc = s.get('description') or "Без описания"
                s_price = s.get('price') or "0"
                text += f"{i}. <b>{html.escape(str(s_name))}</b>\n"
                text += f"   <i>Описание</i>: {html.escape(str(s_desc))}\n"
                text += f"   <i>Прайс</i>: {html.escape(str(s_price))}\n\n"
            else:
                text += f"{i}. ⚠️ <b>[Некорректный формат услуги]</b>: <code>{html.escape(str(s))}</code>\n\n"
    else:
        text += "<b>Услуги отсутствуют.</b>\n"

    return text

def format_deal_auto_cancelled_alert(deal_id: str, client_id, provider_id, service_name: str, price: float, reason: str, users_db: dict, profiles_db: dict) -> str:
    """Форматирует алерт автоматической отмены сделки по таймауту для модератора."""
    c_display = _get_user_display_name(client_id, users_db, profiles_db)
    p_display = _get_user_display_name(provider_id, users_db, profiles_db)

    return (
        f"🛑 <b>Авто-отмена сделки по таймауту</b> 🛑\n"
        f"ID Сделки: <code>{deal_id}</code>\n"
        f"👤 <b>Заказчик:</b> {html.escape(c_display)} (ID: <code>{client_id}</code>)\n"
        f"🛠 <b>Исполнитель:</b> {html.escape(p_display)} (ID: <code>{provider_id}</code>)\n"
        f"📦 <b>Услуга:</b> {html.escape(str(service_name))}\n"
        f"💰 <b>Сумма:</b> {price:g} монет\n"
        f"📝 <b>Причина:</b> {html.escape(reason)}"
    )

