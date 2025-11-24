def is_chat(message, allowed_chats: list) -> bool:
    """
    Проверяет, принадлежит ли сообщение к одному из разрешённых чатов.
    это нужно когда сравниваем от кого пришло сообщение чтобы понять это админ/разработчик или пользователь?

    allowed_chats может содержать:
      - username чата (@channel_name или channel_name)
      - chat_id (int или str)
    """
    chat_username = getattr(message.chat, "username", None)
    chat_id = str(message.chat.id)  # всегда приводим id к строке для сравнения

    for chat in allowed_chats:
        if isinstance(chat, int):
            # сравниваем числовой id
            if chat_id == str(chat):
                return True
        elif isinstance(chat, str):
            if chat.startswith("@"):
                # сравнение по username без @
                if chat_username and chat_username.lower() == chat.lstrip("@").lower():
                    return True
            elif chat.isdigit() or (chat.startswith("-") and chat[1:].isdigit()):
                # строковый chat_id
                if chat_id == chat:
                    return True
            else:
                # сравниваем по username без @, если передана строка без @
                if chat_username and chat_username.lower() == chat.lower():
                    return True
        else:
            # неизвестный тип, пропускаем
            continue

    return False