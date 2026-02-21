from enum import Enum

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from services.keyboards.bot_all_buttons import CommandsBot, MainMenuButtons, AdminChatButtons, ModeratorChatButtons, EditProfileButtons


def get_moderator_menu_keyboard() -> InlineKeyboardMarkup:
    """Создаёт кнопку для меню чата с модератором."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=ModeratorChatButtons.VIEW_NEW_APPLICATIONS.value, callback_data=ModeratorChatButtons.VIEW_NEW_APPLICATIONS.name.lower())],
        [InlineKeyboardButton(text=ModeratorChatButtons.EXCLUDE_PARTICIPANT.value, callback_data=ModeratorChatButtons.EXCLUDE_PARTICIPANT.name.lower())],
        [InlineKeyboardButton(text=ModeratorChatButtons.SEND_COINS.value, callback_data=ModeratorChatButtons.SEND_COINS.name.lower())],
        [InlineKeyboardButton(text=ModeratorChatButtons.SHOW_BALANCE.value, callback_data=ModeratorChatButtons.SHOW_BALANCE.name.lower())],
        [InlineKeyboardButton(text=CommandsBot.CLOSE.value, callback_data=CommandsBot.CLOSE.value.lower())]
    ])

def get_inline_keyboard_menu_for_users() -> InlineKeyboardMarkup:
    """
    Возвращает Inline-клавиатуру по вызову всего меню
    """
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                # Первая кнопка
                InlineKeyboardButton(text=MainMenuButtons.VIEW_PROFILE.value, callback_data=MainMenuButtons.VIEW_PROFILE.name.lower()),
                # Твоя новая кнопка EDIT_PROFILE_MENU
                InlineKeyboardButton(text=EditProfileButtons.EDIT_PROFILE_MENU.value, callback_data=EditProfileButtons.EDIT_PROFILE_MENU.name.lower()) 
            ],
            [
                InlineKeyboardButton(text=MainMenuButtons.VIEW_MY_BALANCE.value, callback_data=MainMenuButtons.VIEW_MY_BALANCE.name.lower()),
                InlineKeyboardButton(text=MainMenuButtons.VIEW_OTHERS_BALANCE.value, callback_data=MainMenuButtons.VIEW_OTHERS_BALANCE.name.lower())
            ],
            [
                InlineKeyboardButton(text=MainMenuButtons.VIEW_DEALS_HISTORY.value, callback_data=MainMenuButtons.VIEW_DEALS_HISTORY.name.lower()),
                InlineKeyboardButton(text=MainMenuButtons.FIND_SERVICE.value, callback_data=MainMenuButtons.FIND_SERVICE.name.lower())
            ],
            [
                InlineKeyboardButton(text=MainMenuButtons.CONFIRM_DEAL.value, callback_data=MainMenuButtons.CONFIRM_DEAL.name.lower()),
                InlineKeyboardButton(text=MainMenuButtons.SUPPORT.value, callback_data=MainMenuButtons.SUPPORT.name.lower())
            ],
            [
                # Кнопка закрыть в одну строку в самом конце
                InlineKeyboardButton(text=MainMenuButtons.CLOSE.value, callback_data=CommandsBot.CLOSE.value.lower())
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


def get_find_service_keyboard() -> InlineKeyboardMarkup:
    """Создаёт клавиатуру со списком доступных услуг подтвержденных клиентов."""
    from services.users_utils.all_users_manager import load_all_users
    from services.users_utils.user_profile_manager import load_profiles
    from entity.Enums_entity import UserFields, UserLifecycleStatus, UserProfileFields
    
    users = load_all_users()
    profiles = load_profiles()
    
    keyboard = []
    
    for u_id, u_data in users.items():
        if u_data.get(UserFields.STATUS.value) == UserLifecycleStatus.CLIENT.value:
            u_profile = profiles.get(u_id) or profiles.get(str(u_id))
            if u_profile:
                service_name = u_profile.get(UserProfileFields.SERVICE_NAME.value)
                if service_name:
                    # Создаём кнопку: текст = service_name, callback_data = FIND_SERVICE_уид
                    cb_data = f"{MainMenuButtons.FIND_SERVICE.name.lower()}_{u_id}"
                    keyboard.append([InlineKeyboardButton(text=service_name, callback_data=cb_data)])
                    
    # Добавляем кнопку Закрыть в конец
    keyboard.append([InlineKeyboardButton(text=CommandsBot.CLOSE.value, callback_data=CommandsBot.CLOSE.value.lower())])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_profile_view_keyboard() -> InlineKeyboardMarkup:
    """Создаёт кнопку для просмотра профиля (Редактировать + Закрыть)."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=EditProfileButtons.EDIT_PROFILE_MENU.value, callback_data=EditProfileButtons.EDIT_PROFILE_MENU.name.lower())],
        [InlineKeyboardButton(text=CommandsBot.CLOSE.value, callback_data=CommandsBot.CLOSE.value.lower())]
    ])

def get_service_profile_keyboard(target_uid: str) -> InlineKeyboardMarkup:
    """Создает клавиатуру профиля чужой услуги (Отзывы + Создать сделку + Назад)."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=MainMenuButtons.REVIEWS.value, callback_data=f"{MainMenuButtons.REVIEWS.name.lower()}_{target_uid}")],
        [InlineKeyboardButton(text=MainMenuButtons.CREATE_DEAL.value, callback_data=f"{MainMenuButtons.CREATE_DEAL.name.lower()}_{target_uid}")],
        [InlineKeyboardButton(text=MainMenuButtons.BACK_TO_SERVICES.value, callback_data=MainMenuButtons.BACK_TO_SERVICES.name.lower())],
        [InlineKeyboardButton(text=CommandsBot.CLOSE.value, callback_data=CommandsBot.CLOSE.value.lower())]
    ])
