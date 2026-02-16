#!/bin/bash
echo "Останавливаем бота..."

# Находим PID процесса bot.py и убиваем
pkill -f "python3 barter_bot"

# Если запускаешь через run_bot.sh, убей и его
pkill -f "run_barter_bot.sh"

echo "Бот остановлен."
x