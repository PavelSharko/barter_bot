#!/bin/bash
echo "Останавливаем бота..."

# Находим PID процесса bot.py и убиваем
pkill -f "python3 bot.py"

# Если запускаешь через run_bot.sh, убей и его
pkill -f "run_bot_cakes_bot.sh"

echo "Бот остановлен."
x