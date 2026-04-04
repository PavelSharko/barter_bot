from enum import Enum

"""
В этом файле содержатся перечисления (Enum) всех команд и кнопок бота.

Для каждой логической группы команд бота следует создавать свой класс Enum,
чтобы структурировать и разделять команды по назначению и области использования.

Примеры групп:
- Admin_chat_Buttons — кнопки для админского чата.
- CommandsBot — общие команды бота.
- SubprocessMenu — команды для отдельно выделенных процессов или подтем.

Такой подход упрощает сопровождение кода, делает его более читаемым и расширяемым.
"""

# --- Команды бота для админа ---
class AdminChatButtons(str, Enum):
    BUTTON1 = "просто_кнопка1"
    BUTTON2 = "просто_кнопка2"
    BUTTON_FOR_INSERT_ANYTHING = "вставить_текст_фото"

class ModeratorChatButtons(str, Enum):
    MENU = "меню модератора"
    VIEW_NEW_APPLICATIONS = "Просмотреть новые заявки"
    EXCLUDE_PARTICIPANT = "Исключить участника"
    SEND_COINS = "Начислить монеты"
    SHOW_BALANCE = "Мой баланс"
    ROLLBACK_DEAL = "откат сделки🛑"



# --- Команды бота общие ---
class CommandsBot(str, Enum):
    CANCEL = "отмена 🛑"
    CLOSE = "закрыть ❌"
    STOP_BOT = "❌ остановка бота"
    START = "/start"
    MENU = "МЕНЮ БОТА"

# --- Команды главного меню ---
class MainMenuButtons(str, Enum):
    VIEW_PROFILE = "Посмотреть свой профиль 👤"
    VIEW_MY_BALANCE = "Мой баланс 💰"
    VIEW_OTHERS_BALANCE = "Баланс других 👥"
    VIEW_DEALS_HISTORY = "История сделок 📜"
    FIND_SERVICE = "Найти услугу/товар 🔍"
    CONFIRM_DEAL = "Активные сделки ✅"
    SUPPORT = "Поддержка 🆘"
    REVIEWS = "отзывы"
    CHOOSE_DEAL = "Выбрать услугу"
    CREATE_DEAL = "заказать"
    BACK_TO_SERVICES = "назад к другим"
    ACCEPT_TERMS = "принимаю условия"
    ACCEPT_REQUEST = "принять запрос"
    REJECT_REQUEST = "отклонить запрос"

# --- Команды для процесса сделки---
class DealProcessButtons(str, Enum):
    CANCEL_DEAL = "ОТМЕНИТЬ ЗАПИСЬ🛑"
    SERVICE_DONE = "услуга оказана✅"
    LEAVE_REVIEW = "поставить рейтинг ⭐️"
    LEAVE_REVIEW_CLIENT = "написать отзыв 📝"

# --- Команды процесса отзывов ---
class ReviewProcessButtons(str, Enum):
    STAR_1 = "1⭐️"
    STAR_2 = "2⭐️"
    STAR_3 = "3⭐️"
    STAR_4 = "4⭐️"
    STAR_5 = "5⭐️"
    ADD_TEXT_REVIEW = "добавить текст отзыва"

# --- Команды редактирования профиля ---
class EditProfileButtons(str, Enum):
    EDIT_NAME = "ИМЯ"
    EDIT_AREA = "район"
    EDIT_ABOUT = "о себе"
    EDIT_SERVICES = "редактировать услуги"
    CONFIRM_EDIT_PROFILE = "да, редактировать"
    CANCEL_EDIT_PROFILE = "нет не хочу изменять"
    EDIT_PRICE = "прайс"
    SAVE_CHANGES = "сохранить изменения"
    ACCEPT_CHANGES = "принять изменения"
    REJECT_CHANGES = "отклонить изменения"
    EDIT_PROFILE_MENU = "Редактировать профиль ✏️"


class ProcessChangingProfileButtons(str, Enum):
    EDIT_NAME = "edit_name"
    EDIT_AREA = "edit_area"
    EDIT_PROFESSION = "edit_profession"
    EDIT_DESCRIPTION = "edit_desc"
    EDIT_SERVICES = "edit_services"
    EDIT_SOCIALS = "edit_socials"
    FINISH_EDITING = "закончить редактирование ✅"
    # CONTINUEEDITING_EDITING = "продолжить редактирование ✏️"
    # Кнопки для управления услугами
    EDIT_SERVICE = "edit_single_service"
    DELETE_SERVICE = "delete_single_service"
    ADD_SERVICE = "add_new_service"
    BACK_TO_EDIT_MENU =  "продолжить редактирование ✏️"
    BACK_TO_PREW_EDIT_MENU ="назад"
    CANCEL_CHANGES = "отменить изменения ❌"   
    EDIT_SERVICE_NAME_INPUT = "edit_svc_name_input"
    EDIT_SERVICE_DESC_INPUT = "edit_svc_desc_input"
    EDIT_SERVICE_PRICE_INPUT = "edit_svc_price_input"
    # FSM-команды для добавления новой услуги
    ADD_SERVICE_NAME_INPUT = "add_svc_name_input"
    ADD_SERVICE_DESC_INPUT = "add_svc_desc_input"
    ADD_SERVICE_PRICE_INPUT = "add_svc_price_input"




# --- Команды для отдельно выделенного процесса ---
class SubprocessMenu(str, Enum):
    PRODUCT1 = "продукт1"
    PRODUCT2 = "продукт2"
    PRODUCT3 = "продукт3"

class CONTACTED_Menu(str, Enum):
    APPLY_REQUEST = "Подать заявку на вступление"
    ACCEPT_RULES = "Принять правила клуба"
    FILL_PROFILE = "Заполнить анкету участника"
    OK_AGREE = "ок-согласен"

class REJECTED_Menu(str, Enum):
    VIEW_PROFILE = "Просмотр анкеты"
    CLEAR_PROFILE = "Очистить анкету"

class ProfileRegistration_Menu(str, Enum):
    ENTER_NAME = "Ввести ФИО"
    ENTER_AREA = "Указать район"
    ENTER_NAME_PROFESSION = "Указать деятельность"
    ENTER_FULL_INFO_PROFESSION = "описать деятельность"
    ADD_NAME_PRODUCT = "добавить услугу"
    ADD_INFO_PRODUCT = "описать детали услуги"
    ALL_SERVICES_FILLED = "все услуги запонены"

    ENTER_PRICE = "Указать прайс"
    ENTER_SOCIALS = "Указать ссылки и отзывы"
    FINAL_PROFILE_VIEW = "Посмотреть анкету"
    RESTART_PROFILE = "заполнить заново анкету" # Для просмотра готовой анкеты
    SEND_TO_REVIEW = "Отправить на проверку"
    ACCEPT = "принять"
    REJECT = "отклонить"

class CategoryButtons(str, Enum):
    CAT_0 = "category_0"
    CAT_25 = "category_25"
    CAT_50 = "category_50"
    CAT_75 = "category_75"
    CAT_100 = "category_100"

