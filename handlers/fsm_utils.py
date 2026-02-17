# fsm_utils.py

from aiogram import types, Bot
from aiogram.fsm.context import FSMContext
import asyncio

from initApp.config_loader import config
from services.keyboards.creator_persistent_keyboards import get_persistent_main_menu
from services.keyboards.bot_all_buttons import CommandsBot
from services.msgs_utils.deleter_messages import clear_messages
from services.send_msg_utils.utuls_send_msg import safe_send_message
from services.state_bot.global_store import add_message, global_msg_fast, FSM

"""
Утилиты для работы с конечным автоматом состояний (FSM) в Telegram-боте на aiogram.

Файл содержит функции для управления состояниями пользователя, таймерами ожидания ввода,
а также для обработки команды отмены и визуализации прогресса ввода.

active_timers — словарь для отслеживания активных таймеров по chat_id и user_id.
"""


# Словарь для хранения активных таймеров по chat_id
active_timers: dict[tuple[int, int], asyncio.Task] = {}



async def check_cancel_input(text: str, message: types.Message, state: FSMContext) -> bool:
    """
    Проверяет, ввёл ли пользователь команду отмены.
    Если да, очищает FSM и таймер, пишет уведомление и возвращает True.
    Если нет, возвращает False.
    """
    user_id = message.from_user.id
    chat_id = message.chat.id

    if text.lower() == CommandsBot.CANCEL.value.lower():
        add_message(global_msg_fast, message.from_user.id, message)
        msg = await message.reply(
            "🚫 Операция отменена."
        )
        add_message(global_msg_fast, user_id, msg)
        await clear_waiting_input(state, chat_id, user_id)
        return True
    return False






async def add_words_timeout(chat_id: int, user_id: int, state: FSMContext, bot, timeout: int = 60):
    """
    Запускает таймер ожидания ввода с визуальной индикацией прогресса (прогресс-бар).

    Если пользователь не ввёл данные за отведённое время, очищает состояние и информирует.
    Таймер можно отменить вручную (например, при завершении ввода).
    """
    try:
        # Первое сообщение — оставить без изменений
        msg_start: types.Message = await bot.send_message(chat_id, "⏳ Оставшееся время на внесение данных")
        add_message(global_msg_fast, user_id, msg_start)

        # Прогресс-бар отдельным сообщением
        msg_progress: types.Message = await bot.send_message(chat_id, get_progress_bar(timeout, timeout))
        last_progress = None

        update_step = max(1, timeout // 18)

        for i in range(timeout, 0, -update_step):
            current_state = await state.get_state()
            if current_state != FSM.waiting_input.state:
                # пользователь закончил — удаляем прогресс-бар, но не стартовое сообщение
                try:
                    await msg_progress.delete()
                except Exception:
                    pass
                return

            progress = get_progress_bar(timeout, i)
            if progress != last_progress:
                try:
                    await msg_progress.edit_text(progress)
                    last_progress = progress
                except Exception:
                    pass

            await asyncio.sleep(update_step)

        # Время вышло — очищаем состояние, удаляем прогресс-бар, оставляем первое сообщение
        if await state.get_state() == FSM.waiting_input.state:
            await clear_waiting_input(state, chat_id, user_id)
            try:

                await msg_progress.delete()
                await clear_messages(chat_id, global_msg_fast)
                # ✅ это сообщение не идет в чат почему то
                msg_cancel = await bot.send_message(
                    chat_id=chat_id,
                    text=f"⏰ для ввода текста истекло время.\nДля нового вызова команд нажмите {CommandsBot.MENU.value}"

                )

                # await safe_send_message(
                #     bot,
                #     chat_id=chat_id,
                #     text="🍰",
                #     reply_markup=get_persistent_main_menu()
                # )
                # add_message(global_msg_fast, user_id, msg_cancel)


            except Exception:
                pass




    except asyncio.CancelledError:
        # Таймер отменён вручную — удаляем только прогресс-бар
        try:


            await clear_messages(chat_id, global_msg_fast)

        except Exception:
            pass
        return

    finally:
        # Удаляем прогресс-бар всегда
        try:
            await msg_progress.delete()
        except Exception:
            pass
        active_timers.pop((chat_id, user_id), None)

# Установка состояния с запуском таймера
async def set_waiting_input(
        state: FSMContext,
        bot,
        chat_id: int,
        user_id: int,
        command_name: str,
        timeout: int = 60
):
    """
    Устанавливает состояние ожидания ввода данных от пользователя.
    Сбрасывает предыдущие состояния и таймеры, запускает новый таймер по указанному времени.
    """
    # 1️⃣ Сбрасываем старое состояние и таймер
    await clear_waiting_input(state, chat_id, user_id)

    # 2️⃣ Устанавливаем новое состояние
    await state.set_state(FSM.waiting_input)
    await state.update_data(current_command=command_name)

    # 3️⃣ Запускаем новый таймер
    task = asyncio.create_task(add_words_timeout(chat_id, user_id, state, bot, timeout))
    active_timers[(chat_id, user_id)] = task

# Очистка состояния и отмена таймера
async def clear_waiting_input(state: FSMContext, chat_id: int, user_id: int):
    """
    Очищает состояние FSM пользователя и отменяет активный таймер ожидания ввода.
    """
    await state.clear()

    # Удаляем прогресс-бар, если он есть
    msg_progress = active_timers.get((chat_id, user_id))
    if msg_progress:
        try:
            await msg_progress.delete()
        except Exception:
            pass
        active_timers.pop((chat_id, user_id), None)


    # Отменяем таймер для конкретного пользователя
    task = active_timers.get((chat_id, user_id))
    if task and not task.done():
        task.cancel()
    active_timers.pop((chat_id, user_id), None)



def get_progress_bar(total: int, remaining: int, length: int = config.period_change_timer_bar) -> str:
    """
    Формирует строку прогресс-бара для отображения оставшегося времени.
    Возвращает строку вида: "⏳■■■■□□□ 30 сек."
    """
    filled = int((total - remaining) / total * length)
    bar = "■" * filled + "□" * (length - filled)
    return f"⏳ {bar} {remaining} сек."