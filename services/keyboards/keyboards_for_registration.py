from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from services.keyboards.bot_all_buttons import CONTACTED_Menu, ProfileRegistration_Menu, CommandsBot, CategoryButtons
from entity.Enums_entity import UserCategory


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


def get_product_name_keyboard() -> InlineKeyboardMarkup:
    keyboard = [[
        InlineKeyboardButton(
            text=ProfileRegistration_Menu.ENTER_NAME_PROFESSION.value,
            callback_data=ProfileRegistration_Menu.ENTER_NAME_PROFESSION.name.lower()
        )
    ]]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_product_desc_keyboard() -> InlineKeyboardMarkup:
    keyboard = [[
        InlineKeyboardButton(
            text=ProfileRegistration_Menu.ENTER_FULL_INFO_PROFESSION.value,
            callback_data=ProfileRegistration_Menu.ENTER_FULL_INFO_PROFESSION.name.lower()
        )
    ]]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_add_service_keyboard(is_first: bool = True) -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(
                text=ProfileRegistration_Menu.ADD_NAME_PRODUCT.value,
                callback_data=ProfileRegistration_Menu.ADD_NAME_PRODUCT.name.lower()
            )
        ]
    ]
    if not is_first:
        keyboard.append([
            InlineKeyboardButton(
                text=ProfileRegistration_Menu.ALL_SERVICES_FILLED.value,
                callback_data=ProfileRegistration_Menu.ALL_SERVICES_FILLED.name.lower()
            )
        ])
    keyboard.append([
        InlineKeyboardButton(
            text=ProfileRegistration_Menu.RESTART_PROFILE.value,
            callback_data=ProfileRegistration_Menu.RESTART_PROFILE.name.lower()
        )
    ])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_add_info_product_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(
                text=ProfileRegistration_Menu.ADD_INFO_PRODUCT.value,
                callback_data=ProfileRegistration_Menu.ADD_INFO_PRODUCT.name.lower()
            )
        ],
        [
            InlineKeyboardButton(
                text=ProfileRegistration_Menu.RESTART_PROFILE.value,
                callback_data=ProfileRegistration_Menu.RESTART_PROFILE.name.lower()
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_price_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(
                text=ProfileRegistration_Menu.ENTER_PRICE.value,
                callback_data=ProfileRegistration_Menu.ENTER_PRICE.name.lower()
            )
        ],
        [
            InlineKeyboardButton(
                text=ProfileRegistration_Menu.RESTART_PROFILE.value,
                callback_data=ProfileRegistration_Menu.RESTART_PROFILE.name.lower()
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_socials_keyboard() -> InlineKeyboardMarkup:
    keyboard = [[
        InlineKeyboardButton(
            text=ProfileRegistration_Menu.ENTER_SOCIALS.value,
            callback_data=ProfileRegistration_Menu.ENTER_SOCIALS.name.lower()
        )
    ]]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_final_profile_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(
                text=ProfileRegistration_Menu.SEND_TO_REVIEW.value,
                callback_data=ProfileRegistration_Menu.SEND_TO_REVIEW.name.lower()
            )
        ],
        [
            InlineKeyboardButton(
                text=ProfileRegistration_Menu.FINAL_PROFILE_VIEW.value,
                callback_data=ProfileRegistration_Menu.FINAL_PROFILE_VIEW.name.lower()
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_profile_review_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(
                text=ProfileRegistration_Menu.SEND_TO_REVIEW.value,
                callback_data=ProfileRegistration_Menu.SEND_TO_REVIEW.name.lower()
            )
        ],
        [
            InlineKeyboardButton(
                text=ProfileRegistration_Menu.RESTART_PROFILE.value,
                callback_data=ProfileRegistration_Menu.RESTART_PROFILE.name.lower()
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_moderator_approval_keyboard(user_id: int) -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(
                text=ProfileRegistration_Menu.ACCEPT.value,
                callback_data=f"{ProfileRegistration_Menu.ACCEPT.name.lower()}_{user_id}"
            ),
            InlineKeyboardButton(
                text=ProfileRegistration_Menu.REJECT.value,
                callback_data=f"{ProfileRegistration_Menu.REJECT.name.lower()}_{user_id}"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_rejected_keyboard() -> InlineKeyboardMarkup:
    """
    Инлайн-клавиатура после просмотра анкеты:
    - посмотреть анкету ещё раз
    - начать заполнение заново
    """
    keyboard = [
        [
            InlineKeyboardButton(
                text=ProfileRegistration_Menu.FINAL_PROFILE_VIEW.value,
                callback_data=ProfileRegistration_Menu.FINAL_PROFILE_VIEW.name.lower()
            )
        ],
        [
            InlineKeyboardButton(
                text=ProfileRegistration_Menu.RESTART_PROFILE.value,
                callback_data=ProfileRegistration_Menu.RESTART_PROFILE.name.lower()
            )
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)




def get_category_keyboard() -> InlineKeyboardMarkup:
    """
    Инлайн-клавиатура для выбора категории:
    0 / 25 / 50 / 75 / 100 (по 2 в строке, последняя строка — только 100),
    внизу кнопка 'закрыть ❌'.
    """
    keyboard = [
        [
            InlineKeyboardButton(
                text=str(UserCategory.CAT_0.value),
                callback_data=CategoryButtons.CAT_0.value
            ),
            InlineKeyboardButton(
                text=str(UserCategory.CAT_25.value),
                callback_data=CategoryButtons.CAT_25.value
            ),
        ],
        [
            InlineKeyboardButton(
                text=str(UserCategory.CAT_50.value),
                callback_data=CategoryButtons.CAT_50.value
            ),
            InlineKeyboardButton(
                text=str(UserCategory.CAT_75.value),
                callback_data=CategoryButtons.CAT_75.value
            ),
        ],
        [
            InlineKeyboardButton(
                text=str(UserCategory.CAT_100.value),
                callback_data=CategoryButtons.CAT_100.value
            ),
        ],
        [
            InlineKeyboardButton(
                text=CommandsBot.CLOSE.value,
                callback_data=CommandsBot.CLOSE.value
            )
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)






