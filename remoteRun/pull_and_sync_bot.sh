#!/bin/bash

MAIN_DIR="$HOME/cakes_bot"

echo "📥 [INFO] Обновление кода из Git: $MAIN_DIR"

cd "$MAIN_DIR" || { echo "❌ [ERROR] Не удалось перейти в $MAIN_DIR"; exit 1; }

# сохраняем старый HEAD, чтобы сравнить после pull
OLD_HEAD=$(git rev-parse HEAD)

if git pull origin main; then
  echo "✅ [SUCCESS] Код успешно обновлён из репозитория"

  NEW_HEAD=$(git rev-parse HEAD)

  if [ "$OLD_HEAD" != "$NEW_HEAD" ]; then
    echo "📝 [COMMIT] Новый коммит:"
    git --no-pager log -1 --oneline

    echo "📄 [FILES] Изменённые файлы:"
    git diff --name-status "$OLD_HEAD" "$NEW_HEAD"
  else
    echo "ℹ️ [INFO] Новых изменений не было (ветка уже актуальна)."
  fi
else
  echo "❌ [ERROR] Ошибка при git pull"
  exit 1
fi