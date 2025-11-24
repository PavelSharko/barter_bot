# config_loader.py
import sys
import yaml
from pathlib import Path
from types import SimpleNamespace

"""
Загрузка и парсинг конфигурации из YAML файла.

Этот модуль читает файл config.yaml, расположенный на два уровня выше текущего файла,
загружает конфигурационные данные и предоставляет удобный объект `config` для доступа к параметрам.

Особенности:
- Поддержка нескольких окружений (стендов), например: prod, test, dev.
- Выбор активного стенда через аргументы командной строки (второй аргумент),
  либо fallback к значению "default" из config.yaml (по умолчанию "test").
- Объединяет общие параметры (common) с параметрами выбранного стенда (environments).
- Создаёт объект SimpleNamespace для удобного доступа к настройкам как к атрибутам.

Функция get_stend() возвращает название текущего активного стенда.

Такой подход облегчает управление конфигурацией и переключение между окружениями.
"""


CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.yaml"

# Загружаем YAML
with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    _raw_cfg = yaml.safe_load(f)

# Определяем стенд (из аргументов или из default)
if len(sys.argv) >= 3:
    STEND = sys.argv[2]
else:
    STEND = _raw_cfg.get("default", "test")

common = _raw_cfg.get("common", {})
env_cfg = _raw_cfg.get("environments", {}).get(STEND, {})
config_dict = {**common, **env_cfg}

# Глобальный объект-конфиг
config = SimpleNamespace(**config_dict)


def get_stend():
    return STEND