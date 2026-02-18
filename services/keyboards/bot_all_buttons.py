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



# --- Команды бота общие ---
class CommandsBot(str, Enum):
    CANCEL = "отмена 🛑"
    CLOSE = "закрыть ❌"
    STOP_BOT = "❌ остановка бота"
    START = "/start"
    MENU = "МЕНЮ БОТА"

# --- Команды главного меню ---
class MainMenuButtons(str, Enum):
    EX_BUTTON1 = "просто_кнопка1"
    EX_BUTTON2 = "просто_кнопка2"
    EX_BUTTON_FOR_INSERT_ANYTHING = "вставить_текст_фото"



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
    ENTER_NAME_PRODUCT = "Указать товар / услугу"
    ENTER_FULL_INFO_PRODUCT = "описать услугу"
    ENTER_PRICE = "Указать прайс"
    ENTER_SOCIALS = "Указать ссылки и отзывы"
    FINAL_PROFILE_VIEW = "Посмотреть анкету"
    RESTART_PROFILE = "заполнить заново" # Для просмотра готовой анкеты
    SEND_TO_REVIEW = "Отправить на проверку"
    ACCEPT = "принять"
    REJECT = "отклонить"

class CategoryButtons(str, Enum):
    CAT_0 = "category_0"
    CAT_25 = "category_25"
    CAT_50 = "category_50"
    CAT_75 = "category_75"
    CAT_100 = "category_100"
