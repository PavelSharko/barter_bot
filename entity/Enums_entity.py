from enum import Enum

class SomeClass(str, Enum):
    """
    Класс для описания полей будущих сущностей.
    Здесь показан пример с тремя основными полями:
    - ORDER_ID: уникальный идентификатор заказа
    - CUSTOMER_NAME: имя клиента
    - DATE_CREATED: дата создания заказа
    """
    ORDER_ID = "order_id"
    CUSTOMER_NAME = "customer_name"
    DATE_CREATED = "date_created"

class UserProfile(str, Enum):
    NAME_TG = "name_tg"
    NAME_REAL = "name_real"
    DATE_REG = "date_reg"
    PHONE = "phone"
    ADDRESS = "address"
