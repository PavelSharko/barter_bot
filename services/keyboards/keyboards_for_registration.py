from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from services.keyboards.bot_all_buttons import CONTACTED_Menu, ProfileRegistration_Menu

def get_accept_rules_keyboard() -> ReplyKeyboardMarkup:
    """
    Клавиатура с одной кнопкой "Принять правила клуба"
    """
    keyboard = [
        [KeyboardButton(text=CONTACTED_Menu.ACCEPT_RULES.value)]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

    

def get_full_name_keyboard() -> InlineKeyboardMarkup:
    """
    Клавиатура для начала регистрации (Ввести ФИО и т.д.)
    """
    keyboard = [
        [
            InlineKeyboardButton(
                text=ProfileRegistration_Menu.ENTER_NAME.value,
                callback_data=ProfileRegistration_Menu.ENTER_NAME.name.lower()  # "enter_name"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_area_keyboard() -> InlineKeyboardMarkup:
    """
    Клавиатура для начала регистрации (Ввести ФИО и т.д.)
    """
    keyboard = [
        [
            InlineKeyboardButton(
                text=ProfileRegistration_Menu.ENTER_AREA.value,
                callback_data=ProfileRegistration_Menu.ENTER_AREA.name.lower()  # "enter_name"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)





