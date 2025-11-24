from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from services.keyboards.bot_all_buttons import CommandsBot


def get_inline_keyboard_close() -> InlineKeyboardMarkup:
    """."""
    return InlineKeyboardMarkup(inline_keyboard=[

        [InlineKeyboardButton(text=CommandsBot.CLOSE.value.lower(), callback_data=CommandsBot.CLOSE.value.lower())]
    ])
