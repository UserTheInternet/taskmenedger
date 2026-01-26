# Taskmenedger MVP

Локальный планер с недельным разворотом и помодоро (MVP) для Windows 10/11.

## Быстрый старт (dev)

```bash
python -m venv .venv
. .venv/Scripts/activate
pip install -r requirements.txt
python -m app.main
```

## Данные

По умолчанию база хранится в `%APPDATA%/Taskmenedger/planner.db`.
Для portable-режима создайте файл `portable.flag` рядом с исполняемым файлом — данные будут в папке `data/`.

## Горячие клавиши

- `Ctrl+S` — сохранить
- `Ctrl+F` — поиск
- `Ctrl+Z` — undo
- `Ctrl+Enter` — новая строка

## Экспорт/импорт

Доступны из панели инструментов.
