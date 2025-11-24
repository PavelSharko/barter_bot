from aiogram import types

async def clear_messages(user_id: int, *storages: dict[int, list[types.Message]]):
    """
    Удаляет все сообщения для конкретного user_id
    из переданных хранилищ (global_msg_fast, global_msg_long и т.д.)
    """
    for storage in storages:
        msgs = storage.get(user_id, [])
        for msg in msgs:
            try:
                await msg.delete()
            except Exception as e:
                print(f"Ошибка удаления сообщения {msg.message_id}: {e}")
        storage[user_id] = []  # очищаем список


