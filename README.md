# Taskmenedger MVP

Локальный планер с недельным разворотом и помодоро (MVP) для Windows 10/11.

## Быстрый старт (dev)

```bash
python -m venv .venv
. .venv/Scripts/activate
pip install -r requirements.txt
python -m app.main
```

## Сборка portable и setup (без Python у пользователя)

### 1) Portable exe (PyInstaller)
```powershell
python -m venv .venv
. .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install pyinstaller
pyinstaller --noconfirm --onefile --windowed --name Taskmenedger app/main.py
```
Готовый файл будет в `dist/Taskmenedger.exe`.

### 2) Setup (Inno Setup)
Установите **Inno Setup 6** и убедитесь, что `iscc.exe` доступен в `PATH`.
Затем выполните:
```powershell
iscc installer\Taskmenedger.iss
```
Готовый установщик будет в `installer/Output/Taskmenedger-Setup.exe`.

### 3) Скрипт сборки одной командой
```powershell
scripts\build_installer.ps1
```

## Обновление кода из Git

Если вы меняете код в репозитории и хотите подтянуть свежие изменения:
```powershell
scripts\update_from_git.ps1 -RepoPath "C:\path\to\taskmenedger" -Branch "main"
```
После обновления пересоберите setup через `scripts\build_installer.ps1`.

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
