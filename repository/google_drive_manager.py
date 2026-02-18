import logging
import os
import shutil
import re
import asyncio
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
from pydrive2.auth import RefreshError

from initApp.config_loader import config
from loggingConfig.colorFormatter import BLUE, RESET, RED

"""
Модуль интеграции с Google Drive для синхронизации файловой базы данных проекта.

Смысл файла:
- Обеспечивает авторизацию в Google Drive с помощью PyDrive2.
- Позволяет загружать локальные данные в облако Google Drive, организуя их в папки копий (copy<N>).
- Позволяет скачивать последние копии из облака в локальную папку.
- Поддерживает регулярную периодическую загрузку обновлений на Google Drive.
- Управляет очисткой старых копий, оставляя последние актуальные.

Каждый основной метод асинхронен и использует asyncio.to_thread для вызова синхронных API PyDrive2 без блокировок.

Важное замечание по настройке:
- Для работы нужно получить файл клиентских секретов Google API `client_secret_XXXX.json` с Google Cloud Console.
- При первом запуске, если не найден `token.json`, откроется браузер для авторизации и создания токена.
- Далее токен будет храниться для автоматического обновления авторизации.
- Для получения client_secret надо зайти на Google Cloud Console, создать проект, включить API Google Drive,
  создать OAuth2 credentials, скачать json файл и положить его в папку проекта под именем CLIENT_SECRET_FILE.
- Без корректного client_secret и успешной авторизации работа с Google Drive невозможна.

"""

"""
Система копирования и синхронизации данных проекта с Google Drive реализована для надежного хранения и резервирования файловой базы приложения.

Ключевые задачи и смысл такой архитектуры:
- **Безопасность данных.** Каждая загрузка (бэкап) данных на Google Drive создает отдельную папку (copy<N>) с новым номером. Это позволяет хранить несколько актуальных копий и быстро восстанавливать данные при сбое или ошибке.
- **Автоматизация.** Все методы построены на асинхронных задачах: копии создаются, устаревшие папки с бэкапами автоматически чистятся, скачивание и загрузка данных выполняется в фоне без блокировки приложения.
- **Минимизация потерь при сбое.** Новая копия всегда создается с инкрементным номером, а старые копии удаляются только если их накопилось слишком много, что снижает риск потери важных данных.
- **Простота восстановления.** Скачивание всегда берёт последнюю созданную (самую свежую) копию, чтобы восстановить рабочее состояние системы.
- **Гибкость.** Параметры копирования, периодичности, количества хранимых копий – всё легко настраивается из централизованного конфига.
**Результат:** Ваши данные всегда оперативно синхронизируются с облаком, а восстановление или обмен между стендами происходит максимально быстро и безопасно без ручных действий.

"""
CLIENT_SECRET_FILE = "client_secret_297858071256-6rfhu45a5m5gnfeg8qbi220segmfgevi.apps.googleusercontent.com.json"
TOKEN_FILE = "token.json"


# ================== Авторизация ==================
async def get_drive():
    """Возвращает авторизованный GoogleDrive.
    Если нет token.json → откроет браузер и создаст его с refresh_token.
    """
    def _get():
        gauth = GoogleAuth()
        gauth.LoadClientConfigFile(CLIENT_SECRET_FILE)
        gauth.settings["get_refresh_token"] = True
        gauth.settings["oauth_scope"] = ["https://www.googleapis.com/auth/drive"]
        gauth.LoadCredentialsFile(TOKEN_FILE)

        try:
            if gauth.credentials is None:
                logging.debug("🔑 Первый запуск → открываю браузер для авторизации...")
                gauth.LocalWebserverAuth()
            elif gauth.access_token_expired:
                gauth.Refresh()
            else:
                gauth.Authorize()
        except RefreshError:
            logging.debug("⚠️ Refresh токен не найден → авторизуйся заново.")
            gauth.LocalWebserverAuth()

        gauth.SaveCredentialsFile(TOKEN_FILE)
        return GoogleDrive(gauth)

    return await asyncio.to_thread(_get)


# ================== Утилиты ==================
async def get_folder_id(drive, folder_name, parent_id=None):
    def _get():
        query = f"title='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
        if parent_id:
            query += f" and '{parent_id}' in parents"

        folder_list = drive.ListFile({
            'q': query,
            'supportsAllDrives': True,
            'includeItemsFromAllDrives': True
        }).GetList()
        return folder_list[0]['id'] if folder_list else None

    return await asyncio.to_thread(_get)


async def get_or_create_subfolder(drive, parent_id, folder_name):
    folder_id = await get_folder_id(drive, folder_name, parent_id)
    if folder_id:
        return folder_id

    def _create():
        folder_metadata = {
            "title": folder_name,
            "mimeType": "application/vnd.google-apps.folder",
            "parents": [{"id": parent_id}],
        }
        folder = drive.CreateFile(folder_metadata)
        folder.Upload(param={'supportsAllDrives': True})
        return folder["id"]

    return await asyncio.to_thread(_create)


async def get_latest_copy_folder(drive, parent_id):
    def _get():
        folder_list = drive.ListFile({
            "q": f"'{parent_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false",
            'supportsAllDrives': True,
            'includeItemsFromAllDrives': True
        }).GetList()

        max_num = 0
        latest_folder_id = None

        for folder in folder_list:
            match = re.match(r"copy(\d+)", folder["title"])
            if match:
                num = int(match.group(1))
                if num > max_num:
                    max_num = num
                    latest_folder_id = folder["id"]

        return latest_folder_id, max_num

    return await asyncio.to_thread(_get)


async def cleanup_old_copies(drive, root_folder_id, keep_last=2, threshold=10, remove_count=8):
    """Удаляет старые copy<N>, оставляет только последние keep_last."""
    def _cleanup():
        folder_list = drive.ListFile({
            "q": f"'{root_folder_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false",
            'supportsAllDrives': True,
            'includeItemsFromAllDrives': True
        }).GetList()

        copies = []
        for folder in folder_list:
            match = re.match(r"copy(\d+)", folder["title"])
            if match:
                copies.append((int(match.group(1)), folder["id"], folder["title"]))

        if len(copies) >= threshold:
            copies.sort(key=lambda x: x[0])  # сортируем по номеру (от старых к новым)
            to_delete = copies[:-keep_last][:remove_count]  # самые старые

            for num, fid, title in to_delete:
                f = drive.CreateFile({'id': fid})
                f.Delete()
                logging.debug(f"🗑 Удалена старая папка: {title}")

    await asyncio.to_thread(_cleanup)


# ================== Основные методы ==================
async def upload_db_folder(local_folder=config.DB_STORGE, drive_folder_name=config.GOOGLE_DRIVE_FOLDER_NAME):
    drive = await get_drive()
    root_folder_id = await get_folder_id(drive, drive_folder_name)
    if not root_folder_id:
        raise Exception(f"❌ Папка '{drive_folder_name}' не найдена!")

    await cleanup_old_copies(drive, root_folder_id)

    latest_folder_id, latest_num = await get_latest_copy_folder(drive, root_folder_id)
    new_num = latest_num + 1
    new_folder_name = f"copy{new_num}"

    new_folder_id = await get_or_create_subfolder(drive, root_folder_id, new_folder_name)
    logging.debug(f"📂 Создана новая папка: {new_folder_name}")

    async def _upload_file(filename):
        file_path = os.path.join(local_folder, filename)
        if os.path.isfile(file_path):
            def _do_upload():
                gfile = drive.CreateFile({"title": filename, "parents": [{"id": new_folder_id}]})
                gfile.SetContentFile(file_path)
                gfile.Upload(param={'supportsAllDrives': True})
                logging.debug(f"✅ Загружен {filename} → {new_folder_name}")
            # тут именно await!
            await asyncio.to_thread(_do_upload)

    await asyncio.gather(*(_upload_file(f) for f in os.listdir(local_folder)))
    return True


async def download_db_folder(local_folder=config.DB_STORGE, drive_folder_name=config.GOOGLE_DRIVE_FOLDER_NAME, keep_tmp=False):
    drive = await get_drive()
    root_folder_id = await get_folder_id(drive, drive_folder_name)
    if not root_folder_id:
        raise Exception(f"❌ Папка '{drive_folder_name}' не найдена!")

    latest_folder_id, latest_num = await get_latest_copy_folder(drive, root_folder_id)
    if not latest_folder_id:
        raise Exception("❌ Нет папок вида copy<N>!")

    latest_folder_name = f"copy{latest_num}"
    logging.debug(f"⬇️ Скачиваем из папки: {latest_folder_name}")

    tmp_folder = f"{local_folder}_tmp"

    def _prepare_tmp():
        if os.path.exists(tmp_folder):
            shutil.rmtree(tmp_folder)
        os.makedirs(tmp_folder, exist_ok=True)

    await asyncio.to_thread(_prepare_tmp)

    def _download_all():
        file_list = drive.ListFile({
            "q": f"'{latest_folder_id}' in parents and trashed=false",
            'supportsAllDrives': True,
            'includeItemsFromAllDrives': True
        }).GetList()

        for file in file_list:
            file.GetContentFile(os.path.join(tmp_folder, file["title"]))
            logging.debug(f"⬇️ Скачан {file['title']} → {tmp_folder}")

        if not keep_tmp:
            # если папки local_folder нет — создаём пустую, чтобы os.rename не падал
            if not os.path.exists(local_folder):
                os.makedirs(local_folder, exist_ok=True)

            # если папка существует и не пуста — удаляем
            elif os.path.exists(local_folder):
                shutil.rmtree(local_folder)

            # переименовываем tmp в local_folder
            os.rename(tmp_folder, local_folder)





    await asyncio.to_thread(_download_all)

    if keep_tmp:
        logging.debug(f"📂 Файлы оставлены во временной папке: {tmp_folder}")
    else:
        logging.debug(f"✅ Обновлён локальный бэкап: {local_folder}")





async def periodic_upload(delay=config.TIME_TO_COPY_REPLICA_DB_MIN*60):
    prepeared_timeout = config.TIME_TO_COPY_REPLICA_DB_MIN
    logging.debug(f"⏳ {BLUE}запуск процесса копирования всех данных на гугл диск - \n\n первая копия череез {prepeared_timeout} минут перед загрузкой бэкапа...{RESET}")
    await asyncio.sleep(prepeared_timeout * 60)

    while True:
        try:


            logging.debug("🚀 Запуск копи в гугл диск()...")
            await upload_db_folder()
            logging.debug("✅ копи в гугл диск() завершён")
            await asyncio.sleep(delay)

        except Exception as e:
            logging.error(f"❌ {RED} Ошибка в periodic_upload:  в записи в гугл диск {e} {RESET}")
            # подождём немного, чтобы не крутиться в цикле при ошибке
            await asyncio.sleep(30)