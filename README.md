ИЗМЕНЕННЫЕ ФАЙЛЫ (последнее обновление):
- README.md
- scripts/export_web_files.py

# Taskmenedger MVP

Локальный планировщик в стиле weekly paper (похоже на tweek.so) с PWA-режимом и хранением задач в Markdown-vault.

## Быстрый запуск web-версии (Windows)

1. Положите файлы проекта в одну папку.
2. Запустите `start_web_planner.bat`.
3. Откройте `http://127.0.0.1:8765/index.html`.
4. Нажмите **Выбрать Vault** и укажите папку-хранилище.

> Для Vault нужен Chromium-браузер (Chrome/Edge/Яндекс) с File System Access API.

## Если открывается старая версия или в логах есть 404 на `/css` и `/js`

Причина: запускается неполный набор файлов (только `index.html`, без папок `css/` и `js/`).

Соберите и копируйте web-версию только так:

```bash
python3 scripts/export_web_files.py
```

После этого берите папку `dist/weekly-planner-pwa/` целиком (вместе с `css/`, `js/`, `start_web_planner.bat`).

## Vault-структура (как в Obsidian)

После выбора папки автоматически создаются:

```text
/vault
  /weeks
  /people
  inbox.md
  someday.md
  config.json
```

- Недельные задачи пишутся в `weeks/YYYY-Www.md`.
- Сотрудники — в `people/<Имя>.md`.
- Someday-задачи — в `someday.md`.

## Импорт старых данных

В шапке приложения есть кнопка **Импортировать из старого localStorage**.
Она переносит данные из старого ключа `weekly-planner-russian-v2` в Markdown vault.

## Архитектура web-клиента

```text
index.html
css/styles.css
js/app.js
js/ui/render.js
js/ui/events.js
js/domain/task.js
js/domain/employee.js
js/storage/vaultFs.js
js/storage/vaultIndex.js
js/utils/date.js
js/utils/md.js
sw.js
manifest.webmanifest
icon.svg
start_web_planner.bat
```

## PWA

- Приложение работает офлайн.
- Service Worker кэширует только фронтенд-ассеты.
- Содержимое vault не кэшируется Service Worker.
