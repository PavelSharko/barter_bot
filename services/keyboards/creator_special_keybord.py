import re
from enum import Enum
from typing import List

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from services.keyboards.bot_all_buttons import CommandsBot




def create_inline_keyboard_from_enum(enum_items: List[Enum], buttons_per_row: int = 2) -> InlineKeyboardMarkup:
    """
    todo убрать это
    Универсальный метод для создания inline клавиатуры из списка элементов Enum.

    Аргументы:
        enum_items (List[Enum]): список элементов Enum, из которых нужно создать кнопки.
        buttons_per_row (int): количество кнопок в одном ряду (по умолчанию 2).

    Возвращает:
        InlineKeyboardMarkup с кнопками, где каждая кнопка создана из enum элемента:
        текст — из enum_item.value,
        callback_data — из enum_item.name в нижнем регистре.

    Позволяет гибко создавать клавиатуры с нужным количеством кнопок в ряду,
    не создавая для каждой клавиатуры отдельные функции.
    """
    keyboard = []
    row = []

    for i, item in enumerate(enum_items, start=1):
        button = InlineKeyboardButton(text=item.value, callback_data=item.name.lower())
        row.append(button)
        if i % buttons_per_row == 0:
            keyboard.append(row)
            row = []

    if row:  # если остались кнопки без полного ряда, добавить их как последний ряд
        keyboard.append(row)

    return InlineKeyboardMarkup(inline_keyboard=keyboard)