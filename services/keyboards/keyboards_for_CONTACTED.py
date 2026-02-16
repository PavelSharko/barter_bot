from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from services.keyboards.bot_all_buttons import CONTACTED_Menu, REJECTED_Menu



# персисентная 
def get_contacted_keyboard() -> ReplyKeyboardMarkup:
    # Создаем клавиатуру с кнопками из CONTACTED_Menu
    keyboard = [
        [KeyboardButton(text=CONTACTED_Menu.APPLY_REQUEST.value)],
        # [KeyboardButton(text=CONTACTED_Menu.ACCEPT_RULES.value)],
        [KeyboardButton(text=CONTACTED_Menu.FILL_PROFILE.value)]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def get_rejected_keyboard() -> ReplyKeyboardMarkup:
    # Создаем клавиатуру с кнопками из REJECTED_Menu
    keyboard = [
        [KeyboardButton(text=REJECTED_Menu.VIEW_PROFILE.value)],
        [KeyboardButton(text=REJECTED_Menu.CLEAR_PROFILE.value)]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def get_agree_keyboard() -> ReplyKeyboardMarkup:
    # Создаем клавиатуру с кнопкой OK_AGREE
    keyboard = [
        [KeyboardButton(text=CONTACTED_Menu.OK_AGREE.value)]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def get_anketa_keyboard() -> ReplyKeyboardMarkup:
    # Создаем клавиатуру с кнопкой заполнить анкету
    keyboard = [
        [KeyboardButton(text=CONTACTED_Menu.FILL_PROFILE.value)]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

