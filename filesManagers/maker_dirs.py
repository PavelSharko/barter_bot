# maker_dirs.py
import os

"""
В этом файле содержатся утилитарные функции для работы с файловой системой.

Функция ensure_file_directory(folder_file_path: str) проверяет, 
существует ли директория для указанного файла, и если нет – создаёт её. 
Например, если путь 'data/orders.json', то создаст папку 'data/'.

Функция ensure_file_exists(folder_file_path: str) создаёт пустой файл по указанному пути,
если он ещё не существует, при этом также создаёт необходимые директории.

Эти функции помогают подготовить корректную структуру папок и файлов перед записью данных, 
чтобы избежать ошибок в работе с файловой системой.

Такой подход полезен для автоматической подготовки окружения, когда программа должна гарантировать 
наличие нужных директорий и файлов без ручного вмешательства.
"""



def ensure_file_directory(folder_file_path: str):
    """
    Создаёт директорию, если она указана в пути и ещё не существует.
    Например: 'data/orders.json' → создаст папку 'data/'.
    """
    directory = os.path.dirname(folder_file_path)
    if directory and not os.path.exists(directory):   # 🔥 проверка на пустую строку
        os.makedirs(directory, exist_ok=True)


def ensure_file_exists(folder_file_path: str):
    """
    Создаёт пустой файл, если он ещё не существует.
    Также создаёт директорию для файла, если её нет.
    Например: 'data/orders.json' → создаст 'data/' и 'orders.json'.
    """
    ensure_file_directory(folder_file_path)  # создаём директорию при необходимости
    if not os.path.exists(folder_file_path):
        with open(folder_file_path, "w", encoding="utf-8") as f:
            pass  # создаём пустой файл