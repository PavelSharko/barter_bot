from aiogram.types import InputMediaPhoto
from initApp.config_loader import get_stend

"""
Файл содержит идентификаторы фото и медиагрупп для отправки в Telegram в зависимости от стенда (окружения).

Особенности:
- Идентификаторы фото (file_id) уникальны для каждого бота и каждого файла.
- Чтобы получить file_id фотографии, нужно отправить её именно боту, айди которого используется.
- Этот file_id можно поймать, например, с помощью n8n в триггере и сохранить последний айди для использования.
- Бот не может отправлять фото, которые были загружены другому боту — file_id не универсален.
- В зависимости от выбранного стенда ("prod" или "test") используются разные file_id:
    - В "prod" — реальные ID для отправки настоящих фото и альбомов.
    - В "test" — заглушки, чтобы не использовать реальные данные.

Структура:
- SINGLE_EXAMPLE_PHOTO_ID — айди для отправки одного фото.
- media_group — список InputMediaPhoto для отправки нескольких фото в одной медиагруппе.
- album — список строковых айди для альбома из нескольких фото (до 10). wad
"""


stand  = get_stend()

# айдишник для картинок в тестовом боте
TEST_STUB_ID = "AgACAgIAAxkBAAMkaSRdOztxdeD0DmF2vKT9c-8gkm4AAhcMaxv4xylJKY108a-yLjoBAAMCAAN4AAM2BA"
PROD_STUB_ID = "AgACAgIAAxkBAAMkaSRdOztxdeD0DmF2vKT9c-8gkm4AAhcMaxv4xylJKY108a-yLjoBAAMCAAN4AAM2BA"

if stand == "prod":
    # Продакшн значения

    # так задается айди на отправку одной фото
    SINGLE_EXAMPLE_PHOTO_ID = "PROD_STUB_ID"

    # так задается айди на отправку двух фото  в медиа группе
    media_group = [
            InputMediaPhoto(media="PROD_STUB_ID"),
            InputMediaPhoto(media="PROD_STUB_ID")
        ]

    # так задается айди на отправку до 10  фото  в альбоме
    album = [
        "PROD_STUB_ID",
        "PROD_STUB_ID",
        "PROD_STUB_ID"
    ]



if stand == "test":
    # Значения-заглушки для тестов
    START_PHOTO_ID = TEST_STUB_ID
    # для любой фото дублируем имя из prod выше и присваиваем  TEST_STUB_ID