from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton

from services.keyboards.bot_all_buttons import CommandsBot, ModeratorChatButtons

"""
ТУТ СОЗДАЮТСЯ REPLY ТЕКСТОВЫЕ КНОПКИ.
"""

def get_persistent_main_menu() -> ReplyKeyboardMarkup:
    """
    Создаёт клавиатуру с одной кнопкой основного меню для постоянного отображения.

    Клавиатура reply типа с кнопкой CommandsBot.MENU.
    Используется для удобного вызова главного меню пользователем.
    """
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=CommandsBot.MENU.value)]],
        resize_keyboard=True,
        one_time_keyboard=False
    )
    return keyboard



def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    """
    Создаёт reply клавиатуру с одной кнопкой отмены.

    Кнопка текста CommandsBot.CANCEL используется для отмены текущей операции пользователем.
    Такая клавиатура помогает пользователю быстро прервать действие.
    """
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=CommandsBot.CANCEL.value)]],
        resize_keyboard=True,
        one_time_keyboard=False
    )
    return keyboard


def get_persistent_moderator_menu() -> ReplyKeyboardMarkup:
    """
    Создаёт клавиатуру с одной кнопкой меню модератора.
    """
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=ModeratorChatButtons.MENU.value)]],
        resize_keyboard=True,
        one_time_keyboard=False
    )
    return keyboard