#!/bin/bash
set -e

LOG_LEVEL=${1:-INFO}   # первый параметр — уровень логов (по умолчанию INFO)
STEND=${2:-test}       # второй параметр — стенд (по умолчанию test)

# Определяем директорию, где лежит сам скрипт (remoteRun)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Корень проекта — на уровень выше
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
# Путь к виртуальному окружению
VENV_DIR="$PROJECT_DIR/venv"
# requirements.txt — в корне проекта
REQ_FILE="$PROJECT_DIR/requirements.txt"

echo "📁 Корень проекта: $PROJECT_DIR"
echo "📦 Проверка виртуального окружения..."

# Проверяем, есть ли виртуальное окружение
if [ ! -d "$VENV_DIR" ]; then
    echo "🚀 Виртуальное окружение не найдено, создаём..."
    python3 -m venv "$VENV_DIR"
    source "$VENV_DIR/bin/activate"
    echo "📦 Устанавливаем зависимости из $REQ_FILE..."
    pip install --upgrade pip
    pip install -r "$REQ_FILE"
else
    echo "✅ Виртуальное окружение найдено."
    source "$VENV_DIR/bin/activate"
fi

# Проверка что barter_bot существуетв
if [ ! -f "$PROJECT_DIR/barter_bot.py" ]; then
    echo "❌ Ошибка: не найден barter_bot.py в $PROJECT_DIR"
    exit 1
fi

while true; do
    echo "🔎 Проверка: убиваем все старые процессы barter_bot..."
    pkill -f "python3 barter_bot.py" && echo "✅ Старые процессы убиты" || echo "ℹ️ Нет старых процессов"

    echo "🚀 Запуск бота с уровнем логирования $LOG_LEVEL и стендом $STEND..."
    cd "$PROJECT_DIR" || exit 1

    python3 barter_bot.py "$LOG_LEVEL" "$STEND"
    EXIT_CODE=$?
    echo "⚠️ Бот завершился с кодом $EXIT_CODE - перезапуск через 5 секунд..."
    sleep 5
done