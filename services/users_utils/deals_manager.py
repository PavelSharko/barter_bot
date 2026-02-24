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

def has_unreviewed_finished_deals(client_id: int) -> Optional[Tuple[str, str]]:
    """
    Проверяет, есть ли у пользователя (как клиента) завершенные сделки,
    на которые он еще не оставил отзыв.
    Возвращает (ID сделки, название услуги), если такая найдена, иначе None.
    """
    deals = load_deals_locked()
    for deal_id, deal in deals.items():
        if deal.get("status_deal") == "finished" and \
           deal.get("review_already_left") is False and \
           str(deal.get("service_client_id")) == str(client_id):
            return str(deal_id), str(deal.get(DealFields.SERVICE_NAME.value, 'Без названия'))
    return None
