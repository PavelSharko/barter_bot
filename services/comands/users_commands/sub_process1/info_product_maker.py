import asyncio

from aiogram.types import InputMediaPhoto

from pictures.pictures_DB import album, media_group, SINGLE_EXAMPLE_PHOTO_ID
from services.keyboards.sustem_inline_keyboard import get_inline_keyboard_close
from services.utiis.global_store import add_message, global_msg_fast


async def send_all_production_to_user(bot, user_id):
    """
    Отправляет пользователю информацию о всех продуктах с небольшими паузами между отправками.
    Последовательно вызывает методы отправки информации и фотографий по каждому из продуктов.
    """
    await send_product1_info(bot, user_id)
    await asyncio.sleep(1)
    await send_product2_info(bot, user_id)
    await asyncio.sleep(1)
    await send_product3_info(bot, user_id)
    await asyncio.sleep(1)





async def send_product1_info(bot, user_id):
    """
    метод пример
    например так отправить альбом фоток
    """
    media_group = [InputMediaPhoto(media=p) for p in album]
    await bot.send_media_group(chat_id=user_id, media=media_group)

    # Отдельным сообщением — кнопка и текст
    msg = await bot.send_message(
        chat_id=user_id,
        text="инфа продукт 1 и альбом из фоток выше",
        reply_markup=get_inline_keyboard_close()
    )
    add_message(global_msg_fast, user_id, msg)

async def send_product2_info(bot, user_id):
    """
    метод пример
    Отправляем альбом из двух фото
    """
    await bot.send_media_group(chat_id=user_id, media=media_group)

    # Отдельным сообщением — кнопка и текст
    msg = await bot.send_message(
        chat_id=user_id,
        text="инфа продукт 2 и альбом из фоток выше",
        reply_markup=get_inline_keyboard_close()
    )
    add_message(global_msg_fast, user_id, msg)



async def send_product3_info(bot, user_id):
    # так отправляется одна фотка и текст
    msg = await bot.send_photo(
        chat_id=user_id,
        photo=SINGLE_EXAMPLE_PHOTO_ID,
        reply_markup=get_inline_keyboard_close()
    )
    add_message(global_msg_fast, user_id, msg)


