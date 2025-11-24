# loggingConfig/colorFormatter.py
import logging


"""
Кастомный форматтер для логгирования с цветовым отображением уровней логов.

Класс ColorFormatter расширяет стандартный logging.Formatter,
добавляя раскраску строк лога в разные цвета в зависимости от уровня сообщения:

- DEBUG — желтый
- INFO — зеленый
- WARNING — оранжевый
- ERROR и CRITICAL — красный

Цветовые escape-последовательности сбрасываются после каждого сообщения,
чтобы не влиять на последующий вывод.

Такой форматтер улучшает читаемость логов в консоли, позволяя быстро визуально отличать важность сообщений.
"""

RESET = "\x1b[0m"
YELLOW = "\x1b[33m"
GREEN = "\x1b[32m"
ORANGE = "\x1b[38;5;208m"
RED = "\x1b[31m"
BLUE = "\033[94m"
MAGENTA = "\x1b[35m"


class ColorFormatter(logging.Formatter):
    def format(self, record):
        record.asctime = self.formatTime(record, self.datefmt)
        msg = super().format(record)
        if record.levelname == "DEBUG":
            return f"{YELLOW}[{record.asctime}] DEBUG:{RESET} {record.getMessage()}"
        elif record.levelname == "INFO":
            return f"{GREEN}[{record.asctime}] INFO:{RESET} {record.getMessage()}"
        elif record.levelname == "WARNING":
            return f"{ORANGE}{msg}{RESET}"
        elif record.levelname in ("ERROR", "CRITICAL"):
            return f"{RED}{msg}{RESET}"
        return msg

# 👉 экспортируем цвета
__all__ = ["RESET", "YELLOW", "GREEN", "ORANGE", "RED", "BLUE", "MAGENTA"]