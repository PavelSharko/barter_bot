from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from services.keyboards.bot_all_buttons import EditProfileButtons, CommandsBot, MainMenuButtons, ProcessChangingProfileButtons
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
            InlineKeyboardButton(text="О себе", callback_data=EditProfileButtons.EDIT_ABOUT.name.lower()),
            InlineKeyboardButton(text="Прайс", callback_data=EditProfileButtons.EDIT_PRICE.name.lower())
        ],
        [
            InlineKeyboardButton(text="Редактировать услуги", callback_data=EditProfileButtons.EDIT_SERVICES.name.lower())
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

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_confirm_edit_profile_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура подтверждения редактирования профиля."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=EditProfileButtons.CONFIRM_EDIT_PROFILE.value,
                callback_data=EditProfileButtons.CONFIRM_EDIT_PROFILE.name.lower()
            )
        ],
        [
            InlineKeyboardButton(
                text=EditProfileButtons.CANCEL_EDIT_PROFILE.value,
                callback_data=EditProfileButtons.CANCEL_EDIT_PROFILE.name.lower()
            )
        ]
    ])


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

def get_keyboard_for_changing_profile() -> InlineKeyboardMarkup:
    """Полная клавиатура редактирования профиля с блокировкой."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Имя", callback_data=ProcessChangingProfileButtons.EDIT_NAME.name.lower()),
            InlineKeyboardButton(text="Район", callback_data=ProcessChangingProfileButtons.EDIT_AREA.name.lower())
        ],
        [
            InlineKeyboardButton(text="Деятельность", callback_data=ProcessChangingProfileButtons.EDIT_PROFESSION.name.lower()),
            InlineKeyboardButton(text="О себе", callback_data=ProcessChangingProfileButtons.EDIT_DESCRIPTION.name.lower())
        ],
        [
            InlineKeyboardButton(text="Ссылки и соц. сети", callback_data=ProcessChangingProfileButtons.EDIT_SOCIALS.name.lower())
        ],
        [
            InlineKeyboardButton(text="Редактировать услуги", callback_data=ProcessChangingProfileButtons.EDIT_SERVICES.name.lower())
        ],
        [
            InlineKeyboardButton(text="закончить редактирование ✅", callback_data=ProcessChangingProfileButtons.FINISH_EDITING.name.lower())
        ],
        [
            InlineKeyboardButton(text="отменить изменения ❌", callback_data=ProcessChangingProfileButtons.CANCEL_CHANGES.name.lower())
        ]
    ])


def get_still_editing_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура-барьер: пользователь ещё в процессе редактирования."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=ProcessChangingProfileButtons.BACK_TO_EDIT_MENU.value,
                callback_data=ProcessChangingProfileButtons.BACK_TO_EDIT_MENU.name.lower()
            )
        ],
        [
            InlineKeyboardButton(
                text=ProcessChangingProfileButtons.FINISH_EDITING.value.lower(),
                callback_data=ProcessChangingProfileButtons.FINISH_EDITING.name.lower()
            )
        ],
        [
            InlineKeyboardButton(
                text=ProcessChangingProfileButtons.CANCEL_CHANGES.value.lower(),
                callback_data=ProcessChangingProfileButtons.CANCEL_CHANGES.name.lower()
            )
        ]
    ])


def get_service_edit_keyboard(service_idx: int) -> InlineKeyboardMarkup:
    """Клавиатура для одной услуги: «редактировать» / «удалить услугу»."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Редактировать",
                callback_data=f"{ProcessChangingProfileButtons.EDIT_SERVICE.name.lower()}_{service_idx}"
            ),
            InlineKeyboardButton(
                text="Удалить услугу",
                callback_data=f"{ProcessChangingProfileButtons.DELETE_SERVICE.name.lower()}_{service_idx}"
            )
        ]
    ])


def get_services_footer_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура внизу списка услуг: «добавить услугу» + «назад»."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Добавить услугу ➕",
                callback_data=ProcessChangingProfileButtons.ADD_SERVICE.name.lower()
            )
        ],
        [
            InlineKeyboardButton(
                text=ProcessChangingProfileButtons.BACK_TO_PREW_EDIT_MENU.value.lower(),
                callback_data=ProcessChangingProfileButtons.BACK_TO_EDIT_MENU.name.lower()
            )
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
