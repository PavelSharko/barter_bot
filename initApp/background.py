# background.py
import asyncio

from scheduler.scheduler import run_registration_reminders, run_auto_cancel_deals
from scheduler.audit_all_users_scheduler import run_global_audit_scheduler
from services.comands.admin_commands.sender_system_msgs import send_startup_message
from repository.google_drive_manager import download_db_folder, periodic_upload


async def start_background_tasks(loop, bot):
    """
    Запускает важные фоновые задачи при старте бота.

    - Сначала загружает актуальные файлы из Google Диска в локальную базу,
      чтобы данные были свежими перед запуском.
    - Затем создаёт отложенную задачу отправки приветственного сообщения о старте бота.
    - Запускает планировщик (scheduler) для регулярных задач внутри бота.
    - Запускает периодическую задачу загрузки обновлённых данных обратно на Google Диск.

    Все фоновые задачи создаются через loop.create_task для асинхронного и неблокирующего выполнения.
    """
    await download_db_folder()
    loop.create_task(delayed_startup_message(bot))
    loop.create_task(run_registration_reminders(bot))
    loop.create_task(run_auto_cancel_deals(bot))
    loop.create_task(run_global_audit_scheduler(bot))
    loop.create_task(periodic_upload())




async def delayed_startup_message(bot):
    """
    Отправляет приветственное сообщение о старте бота с небольшой задержкой.
    Задержка в 3 секунды даёт время завершить начальную инициализацию и загрузку данных.
    """
    await asyncio.sleep(3)
    await send_startup_message(bot)





