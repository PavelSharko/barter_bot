import json
from filelock import FileLock

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
