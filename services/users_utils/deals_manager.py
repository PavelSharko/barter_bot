import json
from typing import Optional, Tuple
from filelock import FileLock
from entity.Enums_entity import DealFields

from filesManagers.maker_dirs import ensure_file_exists
from initApp.config_loader import config

DEALS_LIST: dict[str, dict] = {}

def load_deals() -> dict[str, dict]:
    """Чтение сделок (без лока)."""
    global DEALS_LIST
    ensure_file_exists(config.DEALS_PATH)
    try:
        with open(config.DEALS_PATH, "r", encoding="utf-8") as f:
            DEALS_LIST = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        DEALS_LIST = {}
    return dict(DEALS_LIST)

def save_deals():
    """Запись сделок (без лока — контроль снаружи)."""
    ensure_file_exists(config.DEALS_PATH)
    with open(config.DEALS_PATH, "w", encoding="utf-8") as f:
        json.dump(
            DEALS_LIST,
            f,
            ensure_ascii=False,
            indent=2
        )

def load_deals_locked() -> dict[str, dict]:
    """Чтение с установкой блокировки FileLock."""
    lock = FileLock(f"{config.DEALS_PATH}.lock")
    with lock:
        return load_deals()

def save_deals_locked(deals_data: dict[str, dict]):
    """Запись с установкой блокировки FileLock."""
    global DEALS_LIST
    lock = FileLock(f"{config.DEALS_PATH}.lock")
    with lock:
        DEALS_LIST = deals_data
        save_deals()

def has_unreviewed_finished_deals(user_id: int) -> Optional[Tuple[str, str]]:
    """
    Проверяет, есть ли у пользователя (как клиента ИЛИ как исполнителя) 
    завершенные сделки, на которые он еще не оставил отзыв.
    Мы идем по всем сделкам и проверяем наличие записи в reviews.json
    """
    from services.users_utils.reviews_manager import load_reviews_locked
    deals = load_deals_locked()
    reviews = load_reviews_locked()
    
    for deal_id, deal in deals.items():
        if deal.get("status_deal") == "finished":
            # Уникальный ID отзыва для этого юзера в этой сделке
            review_key = f"{deal_id}_{user_id}"
            
            # Проверяем, участвовал ли юзер в сделке
            is_client = str(deal.get("service_client_id")) == str(user_id)
            is_provider = str(deal.get("service_provider_id")) == str(user_id)
            
            if (is_client or is_provider) and review_key not in reviews:
                return str(deal_id), str(deal.get(DealFields.SERVICE_NAME.value, 'Без названия'))
    return None
