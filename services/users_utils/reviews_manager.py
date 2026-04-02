import json
import os
import logging
from filelock import FileLock
from initApp.config_loader import config
from filesManagers.maker_dirs import ensure_file_exists

def load_reviews_locked() -> dict:
    """Загрузить отзывы списком словарей из файла (блокирующий)."""
    ensure_file_exists(config.REVIEWS_PATH)
    if not os.path.exists(config.REVIEWS_PATH):
        try:
            with FileLock(f"{config.REVIEWS_PATH}.lock"):
                if not os.path.exists(config.REVIEWS_PATH):
                    with open(config.REVIEWS_PATH, "w", encoding="utf-8") as f:
                        json.dump({}, f, ensure_ascii=False, indent=4)
        except Exception as e:
            logging.error(f"Не удалось инициализировать {config.REVIEWS_PATH}: {e}")
            return {}

    try:
        with FileLock(f"{config.REVIEWS_PATH}.lock"):
            if os.path.getsize(config.REVIEWS_PATH) == 0:
                return {}
            with open(config.REVIEWS_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, Exception) as e:
        logging.error(f"Ошибка загрузки отзывов (файл поврежден или путь неверен): {e}")
        return {}


def save_reviews_locked(reviews_data: dict):
    """Сохранить отзывы в файл (с блокировкой)."""
    ensure_file_exists(config.REVIEWS_PATH)
    try:
        with FileLock(f"{config.REVIEWS_PATH}.lock"):
            with open(config.REVIEWS_PATH, "w", encoding="utf-8") as f:
                json.dump(reviews_data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        logging.error(f"Ошибка сохранения отзывов: {e}")
