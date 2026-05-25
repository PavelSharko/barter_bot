import json
import os
from datetime import datetime
from filelock import FileLock, Timeout

FILE_PATH = 'DB_storge/history_transactions.json'
LOCK_PATH = 'DB_storge/history_transactions.json.lock'

def load_transactions_history():
    """Загружает историю переводов модератора."""
    if not os.path.exists(FILE_PATH):
        # Инициализируем пустой структурой
        initial_data = {"transactions": []}
        save_transactions_history(initial_data)
        return initial_data
        
    lock = FileLock(LOCK_PATH, timeout=5)
    try:
        with lock:
            with open(FILE_PATH, 'r', encoding='utf-8') as file:
                data = json.load(file)
            return data
    except (Timeout, FileNotFoundError, json.JSONDecodeError):
        return {"transactions": []}

def save_transactions_history(data):
    """Сохраняет историю переводов модератора."""
    os.makedirs(os.path.dirname(FILE_PATH), exist_ok=True)
    lock = FileLock(LOCK_PATH, timeout=5)
    try:
        with lock:
            with open(FILE_PATH, 'w', encoding='utf-8') as file:
                json.dump(data, file, ensure_ascii=False, indent=4)
    except Timeout:
        pass

def add_transaction_log(sender_id: str, receiver_id: str, amount: float, description: str = ""):
    """Добавляет новую запись в лог переводов."""
    data = load_transactions_history()
    
    transaction = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "sender_id": str(sender_id),
        "receiver_id": str(receiver_id),
        "amount": amount,
        "description": description
    }
    
    data["transactions"].append(transaction)
    save_transactions_history(data)
