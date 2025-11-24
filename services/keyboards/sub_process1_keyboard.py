from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from services.keyboards.bot_all_buttons import CommandsBot, SubprocessMenu


def get_all_products_menu() -> InlineKeyboardMarkup:
    """
    Возвращает Inline-клавиатуру с разделами продукции
    """
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=SubprocessMenu.PRODUCT1.value,
                    callback_data=SubprocessMenu.PRODUCT1.name.lower()
                ),
                InlineKeyboardButton(
                    text=SubprocessMenu.PRODUCT2.value,
                    callback_data=SubprocessMenu.PRODUCT2.name.lower()
                )
            ],
            [
                InlineKeyboardButton(
                    text=SubprocessMenu.PRODUCT3.value,
                    callback_data=SubprocessMenu.PRODUCT3.name.lower()
                )
            ]
        ]
    )
    return keyboard