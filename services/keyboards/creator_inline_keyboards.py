from enum import Enum

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from services.keyboards.bot_all_buttons import CommandsBot, MainMenuButtons, AdminChatButtons, ModeratorChatButtons, EditProfileButtons, DealProcessButtons, ReviewProcessButtons

def get_moderator_menu_keyboard() -> InlineKeyboardMarkup:
    """Создаёт кнопку для меню чата с модератором."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=ModeratorChatButtons.VIEW_NEW_APPLICATIONS.value, callback_data=ModeratorChatButtons.VIEW_NEW_APPLICATIONS.name.lower())],
        [InlineKeyboardButton(text=ModeratorChatButtons.EXCLUDE_PARTICIPANT.value, callback_data=ModeratorChatButtons.EXCLUDE_PARTICIPANT.name.lower())],
        [InlineKeyboardButton(text=ModeratorChatButtons.SEND_COINS.value, callback_data=ModeratorChatButtons.SEND_COINS.name.lower())],
        [InlineKeyboardButton(text=ModeratorChatButtons.SHOW_BALANCE.value, callback_data=ModeratorChatButtons.SHOW_BALANCE.name.lower())],
        [InlineKeyboardButton(text=ModeratorChatButtons.ROLLBACK_DEAL.value, callback_data=ModeratorChatButtons.ROLLBACK_DEAL.name.lower())],
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
                InlineKeyboardButton(text=CommandsBot.CLOSE.value, callback_data=CommandsBot.CLOSE.value.lower())
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


def get_find_service_keyboard(user_id: int = None) -> InlineKeyboardMarkup:
    """Создаёт клавиатуру со списком доступных услуг подтвержденных клиентов."""
    from services.users_utils.all_users_manager import load_all_users
    from services.users_utils.user_profile_manager import load_profiles
    from entity.Enums_entity import UserFields, UserLifecycleStatus, UserProfileFields
    
    users = load_all_users()
    profiles = load_profiles()
    
    keyboard = []
    
    for u_id, u_data in users.items():
        if u_data.get(UserFields.STATUS.value) in (UserLifecycleStatus.CLIENT.value, UserLifecycleStatus.TIMELY_PROFILE_CHANGE_BLOCKED.value):
            u_profile = profiles.get(u_id) or profiles.get(str(u_id))
            if u_profile:
                # Кнопка теперь показывает имя пользователя и его деятельность (PROFESSION)
                user_name = u_profile.get(UserProfileFields.NAME.value, "Аноним")
                profession = u_profile.get(UserProfileFields.PROFESSION.value, "")
                
                if str(u_id) == str(user_id):
                    user_name = f"(я) {user_name}"
                
                if profession:
                    button_text = f"{user_name}: {profession}"
                else:
                    button_text = user_name
                
                cb_data = f"{MainMenuButtons.FIND_SERVICE.name.lower()}_{u_id}"
                keyboard.append([InlineKeyboardButton(text=button_text, callback_data=cb_data)])
                    
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
    """Создает клавиатуру профиля чужой услуги (Отзывы + Выбрать услугу + Назад)."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=MainMenuButtons.REVIEWS.value, callback_data=f"{MainMenuButtons.REVIEWS.name.lower()}_{target_uid}")],
        [InlineKeyboardButton(text=MainMenuButtons.CHOOSE_DEAL.value, callback_data=f"{MainMenuButtons.CHOOSE_DEAL.name.lower()}_{target_uid}")],
        [InlineKeyboardButton(text=MainMenuButtons.BACK_TO_SERVICES.value, callback_data=MainMenuButtons.BACK_TO_SERVICES.name.lower())],
        [InlineKeyboardButton(text=CommandsBot.CLOSE.value, callback_data=CommandsBot.CLOSE.value.lower())]
    ])

def get_create_deal_for_service_keyboard(target_uid: str, service_idx: int) -> InlineKeyboardMarkup:
    """Создает клавиатуру для заказа конкретной услуги."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=MainMenuButtons.CREATE_DEAL.value, callback_data=f"{MainMenuButtons.CREATE_DEAL.name.lower()}_{target_uid}_{service_idx}")]
    ])

def get_accept_terms_keyboard(provider_uid: str, service_idx: int) -> InlineKeyboardMarkup:
    """Создает клавиатуру для принятия условий сделки."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=MainMenuButtons.ACCEPT_TERMS.value, callback_data=f"{MainMenuButtons.ACCEPT_TERMS.name.lower()}_{provider_uid}_{service_idx}")],
        [InlineKeyboardButton(text=CommandsBot.CLOSE.value, callback_data=CommandsBot.CLOSE.value.lower())]
    ])

def get_provider_deal_action_keyboard(deal_id: str) -> InlineKeyboardMarkup:
    """Создает клавиатуру для исполнителя с ответом на новую сделку."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=MainMenuButtons.ACCEPT_REQUEST.value, callback_data=f"{MainMenuButtons.ACCEPT_REQUEST.name.lower()}_{deal_id}")],
        [InlineKeyboardButton(text=MainMenuButtons.REJECT_REQUEST.value, callback_data=f"{MainMenuButtons.REJECT_REQUEST.name.lower()}_{deal_id}")]
    ])

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_client_deal_keyboard(deal_id: str) -> InlineKeyboardMarkup:
    """Клавиатура для клиента (заказчика) в активной сделке.
    Клиент может:
    - подтвердить, что услуга оказана
    - отменить сделку
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=DealProcessButtons.SERVICE_DONE.value, callback_data=f"{DealProcessButtons.SERVICE_DONE.name.lower()}_{deal_id}")],
        [InlineKeyboardButton(text=DealProcessButtons.CANCEL_DEAL.value, callback_data=f"{DealProcessButtons.CANCEL_DEAL.name.lower()}_{deal_id}")],
    ])


def get_provider_deal_keyboard(deal_id: str) -> InlineKeyboardMarkup:
    """Клавиатура для исполнителя (поставщика) в активной сделке.
    Исполнитель может только запросить отмену.
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=DealProcessButtons.CANCEL_DEAL.value, callback_data=f"{DealProcessButtons.CANCEL_DEAL.name.lower()}_{deal_id}")]
    ])

def get_leave_review_keyboard(deal_id: str) -> InlineKeyboardMarkup:
    """Клавиатура с кнопкой 'Оставить отзыв'."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=DealProcessButtons.LEAVE_REVIEW.value, callback_data=f"{DealProcessButtons.LEAVE_REVIEW.name.lower()}_{deal_id}")]
    ])

def get_review_stars_keyboard(deal_id: str) -> InlineKeyboardMarkup:
    """Клавиатура с 5 звездами рейтинга."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=ReviewProcessButtons.STAR_1.value, callback_data=f"{ReviewProcessButtons.STAR_1.name.lower()}_{deal_id}"),
            InlineKeyboardButton(text=ReviewProcessButtons.STAR_2.value, callback_data=f"{ReviewProcessButtons.STAR_2.name.lower()}_{deal_id}"),
            InlineKeyboardButton(text=ReviewProcessButtons.STAR_3.value, callback_data=f"{ReviewProcessButtons.STAR_3.name.lower()}_{deal_id}"),
            InlineKeyboardButton(text=ReviewProcessButtons.STAR_4.value, callback_data=f"{ReviewProcessButtons.STAR_4.name.lower()}_{deal_id}"),
            InlineKeyboardButton(text=ReviewProcessButtons.STAR_5.value, callback_data=f"{ReviewProcessButtons.STAR_5.name.lower()}_{deal_id}")
        ]
    ])

def get_add_text_review_keyboard(deal_id: str) -> InlineKeyboardMarkup:
    """Клавиатура для добавления текста отзыва."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=ReviewProcessButtons.ADD_TEXT_REVIEW.value, callback_data=f"{ReviewProcessButtons.ADD_TEXT_REVIEW.name.lower()}_{deal_id}")]
    ])
    
def get_reviews_list_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура под списком отзывов."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=MainMenuButtons.BACK_TO_SERVICES.value, callback_data=MainMenuButtons.BACK_TO_SERVICES.name.lower()),
            InlineKeyboardButton(text="закрыть ❌", callback_data="close_menu_bot")
        ]
    ])
