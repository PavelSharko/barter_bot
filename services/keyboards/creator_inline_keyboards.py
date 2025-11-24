from enum import Enum

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from services.keyboards.bot_all_buttons import CommandsBot, MainMenuButtons, AdminChatButtons


def get_inline_keyboard_menu_for_users() -> InlineKeyboardMarkup:
    """
    Возвращает Inline-клавиатуру  по вызову всего меню
    """
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=MainMenuButtons.EX_BUTTON1.value.lower(),
                    callback_data=MainMenuButtons.EX_BUTTON1.value.lower()),
                InlineKeyboardButton(
                    text=MainMenuButtons.EX_BUTTON2.value.lower(),
                    callback_data=MainMenuButtons.EX_BUTTON2.value.lower())
            ],
            [
                InlineKeyboardButton(
                    text=MainMenuButtons.EX_BUTTON_FOR_INSERT_ANYTHING.value.lower(),
                    callback_data=MainMenuButtons.EX_BUTTON_FOR_INSERT_ANYTHING.value.lower())
            ]
        ]
    )
    return keyboard


def get_menu_keyboard_for_developer() -> InlineKeyboardMarkup:
    """Создаёт кнопку для меню чата с девелопером ."""
    return InlineKeyboardMarkup(inline_keyboard=[

        [InlineKeyboardButton(text=CommandsBot.STOP_BOT.value.lower(), callback_data=CommandsBot.STOP_BOT.value.lower())]
    ],
    )


def get_menu_keyboard_for_admin_chat() -> InlineKeyboardMarkup:
    """Создаёт кнопку для меню чата с  админом ."""
    return InlineKeyboardMarkup(inline_keyboard=[

        [InlineKeyboardButton(text=AdminChatButtons.BUTTON1.value.lower(), callback_data=AdminChatButtons.BUTTON1.value.lower())],
        [InlineKeyboardButton(text=AdminChatButtons.BUTTON2.value.lower(), callback_data=AdminChatButtons.BUTTON2.value.lower())],
        [InlineKeyboardButton(text=AdminChatButtons.BUTTON_FOR_INSERT_ANYTHING.value.lower(), callback_data=AdminChatButtons.BUTTON_FOR_INSERT_ANYTHING.value.lower())],

    ],
    )











