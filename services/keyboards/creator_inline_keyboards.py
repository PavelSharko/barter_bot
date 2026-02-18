from enum import Enum

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from services.keyboards.bot_all_buttons import CommandsBot, MainMenuButtons, AdminChatButtons, ModeratorChatButtons


def get_moderator_menu_keyboard() -> InlineKeyboardMarkup:
    """Создаёт кнопку для меню чата с модератором."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=ModeratorChatButtons.VIEW_NEW_APPLICATIONS.value, callback_data=ModeratorChatButtons.VIEW_NEW_APPLICATIONS.name.lower())],
        [InlineKeyboardButton(text=ModeratorChatButtons.EXCLUDE_PARTICIPANT.value, callback_data=ModeratorChatButtons.EXCLUDE_PARTICIPANT.name.lower())],
        [InlineKeyboardButton(text=ModeratorChatButtons.SEND_COINS.value, callback_data=ModeratorChatButtons.SEND_COINS.name.lower())],
        [InlineKeyboardButton(text=ModeratorChatButtons.SHOW_BALANCE.value, callback_data=ModeratorChatButtons.SHOW_BALANCE.name.lower())],
        [InlineKeyboardButton(text=CommandsBot.CLOSE.value, callback_data=CommandsBot.CLOSE.value.lower())]
    ])

# /todo убрать это
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












