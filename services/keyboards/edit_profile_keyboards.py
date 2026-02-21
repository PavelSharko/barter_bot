from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from services.keyboards.bot_all_buttons import EditProfileButtons, CommandsBot, MainMenuButtons
from services.users_utils.all_users_manager import load_all_users
from entity.Enums_entity import UserFlags, ChangesProfileStatus


def get_edit_profile_menu_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """Клавиатура с выбором поля для редактирования с кнопкой закрытия."""
    users = load_all_users()
    user_data = users.get(user_id, {})
    
    keyboard = [
        [
            InlineKeyboardButton(text="Имя", callback_data=EditProfileButtons.EDIT_NAME.name.lower()),
            InlineKeyboardButton(text="Район", callback_data=EditProfileButtons.EDIT_AREA.name.lower())
        ],
        [
            InlineKeyboardButton(text="Название услуги", callback_data=EditProfileButtons.EDIT_NAME_PRODUCT.name.lower()),
            InlineKeyboardButton(text="Прайс", callback_data=EditProfileButtons.EDIT_PRICE.name.lower())
        ],
        [
            # Описание обычно длинное, поэтому оставляем его на всю строку
            InlineKeyboardButton(text="Описание услуги", callback_data=EditProfileButtons.EDIT_FULL_INFO_PRODUCT.name.lower())
        ]
    ]

    # Добавляем кнопку SAVE_CHANGES, если статус PENDING_CHANGES.
    if user_data.get(UserFlags.CHANGES_PROFILE_CONFIRMED.value) == ChangesProfileStatus.PENDING_CHANGES.value:
        keyboard.append([
            InlineKeyboardButton(
                text=EditProfileButtons.SAVE_CHANGES.value, 
                callback_data=EditProfileButtons.SAVE_CHANGES.name.lower()
            )
        ])

    # Добавляем кнопку Закрыть
    keyboard.append([
        InlineKeyboardButton(
            text=CommandsBot.CLOSE.value,
            callback_data=CommandsBot.CLOSE.value.lower()
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_after_edit_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура после редактирования поля (еще что-то или сохранить)."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=EditProfileButtons.EDIT_PROFILE_MENU.value, callback_data=EditProfileButtons.EDIT_PROFILE_MENU.name.lower())
        ],
        [
            InlineKeyboardButton(text=EditProfileButtons.SAVE_CHANGES.value, callback_data=EditProfileButtons.SAVE_CHANGES.name.lower())
        ]
    ])

def get_moderator_approval_changes_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """Клавиатура модератора для утверждения изменений в профиле."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=EditProfileButtons.ACCEPT_CHANGES.value, 
                callback_data=f"{EditProfileButtons.ACCEPT_CHANGES.name.lower()}_{user_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text=EditProfileButtons.REJECT_CHANGES.value, 
                callback_data=f"{EditProfileButtons.REJECT_CHANGES.name.lower()}_{user_id}"
            )
        ]
    ])
