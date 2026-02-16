# Инструкция: Обработка Inline-кнопок с последующим вводом текста

Этот документ описывает стандартный паттерн для сценариев "Нажал кнопку -> Бот очистил чат -> Попросил ввести данные -> Пользователь ввел текст -> Бот сохранил и очистил".

---

## 🏗 Общая архитектура

1.  **Пользователь нажимает Inline-кнопку** (например, "Ввести ФИО").
2.  **`message_handlers.handler_callback`** ловит нажатие:
    *   Сначала проверяются **приоритетные роли** (Разработчик, Модератор) с **конкретными командами**.
    *   Если совпадений нет — код идет дальше к общим обработчикам.
3.  **Inline-handler** (например, `contacted_menu_inline_handler.py`):
    *   **Очищает чат** от старых сообщений (`clear_messages`).
    *   Устанавливает состояние FSM `waiting_input` для конкретной команды.
    *   Отправляет просьбу ввода данных и **сохраняет сообщение** (`add_message`) для будущей очистки.
4.  **Пользователь отправляет текст**.
5.  **`message_handlers.universal_input_handler`** ловит текст (фильтр `FSM.waiting_input`).
6.  **Text-handler** (например, `to_set_profile_commands.py`):
    *   Валидирует и сохраняет данные.
    *   Отправляет подтверждение («Успешно!») и **сохраняет сообщение**.
    *   **Сбрасывает состояние** (`clear_waiting_input`).

---

## 🛠 Детальная реализация

### 1. Объявление команд (Enums)
В `services/keyboards/bot_all_buttons.py`:
```python
class ProfileRegistration_Menu(str, Enum):
    ENTER_NAME = "Ввести ФИО"  # Значение кнопки и имя команды для FSM
```

### 2. Клавиатура (Keyboards)
В `services/keyboards/keyboards_for_registration.py`.
Используйте `Enum.name.lower()` для `callback_data`.

```python
InlineKeyboardButton(
    text=ProfileRegistration_Menu.ENTER_NAME.value,
    callback_data=ProfileRegistration_Menu.ENTER_NAME.name.lower() # "enter_name"
)
```

### 3. Обработка Callback и Приоритеты (Message Handlers)
В `handlers/message_handlers.py` -> `handle_callback`.
**Важно:** Проверки админов/разработчиков должны быть строгими (`if role AND command`), чтобы не перехватывать чужие кнопки.

```python
# 1. Приоритет: Разработчик + Спец. команда
if is_chat(call.message, [config.DEVELOPER_CHAT_ID]):
    if call.data == CommandsBot.STOP_BOT.value.lower():
        await save_actual_data(bot, user_id)
        return  # ВАЖНО: Выход, если команда обработана

# 2. Приоритет: Модератор
if is_chat(call.message, [config.MODERATOR_CONTACT_ID]):
    await handle_callback_from_admin_bot(call, state, bot)
    # Если модератор обрабатывает ВСЕ свои кнопки там, то можно return, или оставить fallthrough

# 3. Общие кнопки (Для всех, включая админов, если они не нажали свои спец. кнопки)
if call.data == CommandsBot.CLOSE.value.lower():
    ...
elif call.data in [item.name.lower() for item in ProfileRegistration_Menu]:
    await handle_profile_registration_callbacks(bot, call, user_id, state)
```

### 4. Inline Handler (Логика и Очистка)
В `services/comands/users_commands/for_contacted/contacted_menu_inline_handler.py`.
Здесь происходит **очистка чата** перед новым диалогом.

```python
async def handle_profile_registration_callbacks(...):
    # 1. Очистка предыдущих сообщений флоу
    await clear_messages(user_id, global_msg_contacted_fast)

    if call.data == ProfileRegistration_Menu.ENTER_NAME.name.lower():
        command_name = ProfileRegistration_Menu.ENTER_NAME.value.lower()
        
        # 2. Установка ожидания ввода
        await set_waiting_input(state, bot, chat_id, user_id, command_name, timeout=...)
        
        # 3. Отправка сообщения и добавление в список на удаление
        msg = await bot.send_message(..., text="🆔 Введите ФИО")
        add_message(global_msg_contacted_fast, user_id, msg)
```

### 5. Прием текста (Universal Input Handler)
В `handlers/message_handlers.py` -> `universal_input_handler`.

```python
data = await state.get_data()
current_command = data.get("current_command")

if current_command == ProfileRegistration_Menu.ENTER_NAME.value.lower():
    # Сообщение пользователя уже будет в global_msg_contacted_fast (если add_message вызывается в text handler или глобально)
    await extract_and_save_full_name_from_msg(message, state, user_id)
```

### 6. Обработка текста (Text Handler)
В `services/comands/users_commands/for_contacted/to_set_profile_commands.py`.

```python
async def extract_and_save_full_name_from_msg(message, state, user_id):
    text = message.text
    
    # 1. Валидация
    if not is_valid(text):
        msg = await message.answer("Ошибка валидации")
        add_message(global_msg_contacted_fast, user_id, msg) # Добавляем ошибку в список на удаление
        return 
        
    # 2. Сохранение
    users[user_id][Field] = text
    save_users()
    
    # 3. Ответ и добавление в список
    msg = await message.answer("Успешно! Следующий шаг...")
    add_message(global_msg_contacted_fast, user_id, msg)
    
    # 4. ОБЯЗАТЕЛЬНО: Сброс состояния (с указанием user_id)
    await clear_waiting_input(state, message.chat.id, user_id)
```
