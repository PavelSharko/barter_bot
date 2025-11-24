# import re
# from typing import Optional, Tuple
#
# USERNAME_RE = re.compile(r'@([a-zA-Z0-9_]{1,32})')  # как в Telegram
# ID_AFTER_LABEL_RE = re.compile(r'(?i)id[^0-9]*([0-9]+)')
# ANY_LONG_NUMBER_RE = re.compile(r'\b([0-9]{5,})\b')  # запасной вариант
#
# def extract_username_and_id(raw: str) -> Tuple[Optional[str], Optional[str]]:
#     """
#     Извлекает username (без @, lower) и user_id (цифры) из произвольной строки.
#     Примеры входа: "@u | ID: `123`", "@u", "id: 123", "123".
#     """
#     if not raw:
#         return None, None
#
#     username = None
#     m = USERNAME_RE.search(raw)
#     if m:
#         username = m.group(1).lower()
#
#     user_id = None
#     m = ID_AFTER_LABEL_RE.search(raw)
#     if m:
#         user_id = m.group(1)
#     else:
#         # если нет явной метки "ID", пытаемся взять первое длинное число
#         m = ANY_LONG_NUMBER_RE.search(raw)
#         if m:
#             user_id = m.group(1)
#
#     return username, user_id