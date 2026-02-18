import json
import os
from datetime import datetime
from threading import Lock
from entity.Enums_entity import BlockingStatusFields

class BlockingManager:
    def __init__(self, storage_path="DB_storge/status_blocking.json"):
        self.storage_path = storage_path
        self.lock = Lock()
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        if not os.path.exists(self.storage_path):
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump({}, f, indent=4, ensure_ascii=False)

    def _load_data(self) -> dict:
        with self.lock:
            try:
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                return {}

    def _save_data(self, data: dict):
        with self.lock:
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)

    def add_block_record(self, user_id: int, moderator_id: int, reason: str, status_before: str, status_after: str) -> str:
        data = self._load_data()
        
        # Generate block ID: b_YYYYMMDD_XXXX
        today_str = datetime.now().strftime("%Y%m%d")
        
        # Find max index for today to increment
        count_today = 0
        prefix = f"b_{today_str}_"
        for key in data.keys():
            if key.startswith(prefix):
                count_today += 1
        
        new_index = count_today + 1
        block_id = f"{prefix}{new_index:04d}" # e.g. b_20260210_0001

        record = {
            BlockingStatusFields.BLOCK_ID.value: block_id,
            BlockingStatusFields.USER_ID.value: user_id,
            BlockingStatusFields.MODERATOR_ID.value: moderator_id,
            BlockingStatusFields.REASON.value: reason,
            BlockingStatusFields.CREATED_AT.value: datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            BlockingStatusFields.STATUS_BEFORE.value: status_before,
            BlockingStatusFields.STATUS_AFTER.value: status_after
        }

        data[block_id] = record
        self._save_data(data)
        return block_id

# Global instance
blocking_manager = BlockingManager()
