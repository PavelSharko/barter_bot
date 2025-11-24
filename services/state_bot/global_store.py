# global_store.py
from typing import Union
import asyncio

from aiogram import types, Bot
from aiogram.fsm.state import State, StatesGroup


"""
Глобальное хранилище для временных данных и состояний, необходимых при обработке сообщений и запуске FSM в Telegram-боте.

Основное предназначение:
- Хранит текущее состояние FSM и вспомогательные глобальные структуры для рассылок, поддержки массовых/многошаговых сценариев.
- Организует каталоги для быстрых и отложенных сообщений по user_id (например, для быстрой очистки чата после команд, массовое удаление, сохранение временных уведомлений и т.п.).
- Содержит набор локов и флагов асинхронного сканирования (например, для предотвращения одновременных операций сканирования и гонки данных).
- Держит ссылку на глобальный бот (устанавливается при инициализации).
- Используется функцией add_message для централизованного и безопасного добавления сообщений в соответствующее хранилище.

Такой подход отделяет логику хранения и работы с временными данными от бизнес-логики, облегчая сопровождение больших FSM- и мультиюнитных проектов на aiogram.
"""


class FSM(StatesGroup):
    waiting_input = State()


# глобальный список сообщений
global_msg_fast: dict[int, list[types.Message]] = {}
global_msg_after_step: dict[int, list[types.Message]] = {}
global_msg_long: dict[int, list[types.Message]] = {}
global_msg_after_order: dict[int, list[types.Message]] = {}
global_msg_delete_after_confirm_order: dict[int, list[types.Message]] = {}



scan_locks: dict[int, asyncio.Lock] = {}
is_scanning: dict[int, bool] = {}

def add_message(storage: dict[int, list[types.Message]], user_id: int, msg: types.Message):
    """Добавляет сообщение в хранилище по user_id"""
    if user_id not in storage:
        storage[user_id] = []
    storage[user_id].append(msg)


# глобальный бот (установится в bot.py)
bot: Union[Bot, None] = None