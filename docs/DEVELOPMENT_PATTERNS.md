# 📚 Паттерны разработки Barter Bot

В этом документе описаны стандарты разработки для поддержания чистоты и стабильности кода.

---

## 1. 🔘 Обработка Callbacks (Кнопок)

### Как создать новую кнопку:
1.  **Добавить в Enum**: Откройте `services/keyboards/bot_all_buttons.py` и добавьте кнопку в соответствующий класс (или создайте новый, если это новая логическая группа).
    ```python
    class MyNewMenu(str, Enum):
        DO_SOMETHING = "Сделать что-то 🚀"
    ```
2.  **Создать клавиатуру**: В `services/keyboards/` используйте этот Enum. `callback_data` должен быть равен `Enum.name.lower()`.
3.  **Зарегистрировать в `message_handlers.py`**:
    В функции `handle_callback` добавьте проверку:
    ```python
    elif call.data in [item.name.lower() for item in MyNewMenu]:
        await my_feature_handler(bot, call, state)
    ```
4.  **Реализовать Handler**: Создайте функцию обработки (желательно в отдельном файле в `handlers/sub_handlers/` или `services/comands/`).

---

## 2. 📝 Обработка Текстовых Команд

### Простые команды (Меню, Старт):
Обрабатываются в `handler_comands_or_simple_msg` в `message_handlers.py`.
Добавляйте `elif text == CommandsBot.MY_COMMAND.value.lower():`.

### Ввод данных (FSM):
Используйте паттерн **Callback -> Input** (см. ниже). Обработка ввода происходит в `universal_input_handler` (фильтр `FSM.waiting_input`).

---

## 3. 🔄 Паттерн "Callback -> Input" (Ввод данных)

Основано на `docs/INSTRUCTION_CALLBACK_INPUT_FLOW.md`. Используется, когда нужно получить текст от пользователя после нажатия кнопки.

**Шаги реализации:**

1.  **Start (Inline Handler)**:
    *   Пользователь жмет кнопку.
    *   Хендлер очищает чат: `await clear_messages(user_id, list_to_clear)`.
    *   Устанавливает состояние FSM: `await set_waiting_input(state, bot, chat_id, user_id, command_name)`.
        *   `command_name` берем из `Enum.value.lower()`.
    *   Отправляет промпт: "Введите ваше имя".
    *   Сохраняет ID сообщения для удаления: `add_message(list_to_clear, user_id, msg)`.

2.  **Input (Message Handler)**:
    *   `universal_input_handler` ловит текст.
    *   Проверяет `current_command` из FSM data.
    *   Направляет в функцию обработки (например, `extract_and_save_data`).

3.  **Process (Logic Service)**:
    *   Получает текст `message.text`.
    *   Валидирует. Если ошибка -> шлет сообщение, добавляет в список удаления, делает `return`.
    *   Сохраняет в JSON/Базу.
    *   Подтверждает успех.
    *   **ВАЖНО**: Сбрасывает состояние `await clear_waiting_input(state, ...)` или переводит в следующее состояние.

---

## 4. 🗃 Работа с JSON и Данными

*   Используются менеджеры в `services/users_utils/` или прямая работа с загруженными данными.
*   При изменении данных пользователя, убедитесь, что вызываете функцию `save_users()` (или аналогичную), чтобы записать изменения из памяти на диск.
*   Пример:
    ```python
    users[user_id]['new_field'] = value
    save_users() # Фиксация изменений
    ```

---

## 5. 🧹 Чистка Чата

Проект стремится к "чистому чату" (без простыни старых сообщений).
*   Используйте `services.msgs_utils.deleter_messages.clear_messages`.
*   Все отправляемые ботом сообщения, которые должны исчезнуть при переходе в другое меню, нужно регистрировать через `add_message(global_msg_list, user_id, message_object)`.
*   Обычно промпты и ошибки добавляются в `global_msg_contacted_fast` или `global_msg_fast`.

---

## 6. 🏗 Создание меню клиента (Заглушки)

Для реализации меню клиента (которое сейчас на заглушках):
1.  Изучите `handlers/sub_handlers/main_menu_handler.py`.
2.  Каждая кнопка из `MainMenuButtons` должна иметь свою ветку логики.
3.  Если функционал сложный (например, "Поиск"), выносите его в отдельный модуль в `services/comands/users_commands/`.
