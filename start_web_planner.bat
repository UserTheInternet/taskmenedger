@echo off
setlocal
cd /d "%~dp0"
chcp 65001 >nul

set MISSING=0
if not exist "index.html" set MISSING=1
if not exist "css\styles.css" set MISSING=1
if not exist "js\app.js" set MISSING=1
if not exist "js\ui\render.js" set MISSING=1
if not exist "js\ui\events.js" set MISSING=1

if "%MISSING%"=="1" (
  echo.
  echo ОШИБКА: Папка неполная. Из-за этого появляются 404 на /css и /js.
  echo.
  echo Что сделать:
  echo 1) Скопируйте ВСЮ папку dist\weekly-planner-pwa целиком.
  echo 2) В этой папке запустите: python verify_web_bundle.py
  echo 3) После COMPLETE снова запустите этот bat-файл.
  echo.
  pause
  exit /b 1
)

echo Запускаю локальный сервер для планировщика...
start "" "http://127.0.0.1:8765/index.html"

where py >nul 2>nul
if %ERRORLEVEL% EQU 0 (
  py -m http.server 8765
  goto :eof
)

where python >nul 2>nul
if %ERRORLEVEL% EQU 0 (
  python -m http.server 8765
  goto :eof
)

where python3 >nul 2>nul
if %ERRORLEVEL% EQU 0 (
  python3 -m http.server 8765
  goto :eof
)

echo.
echo Не найден Python (py/python/python3) в PATH.
echo Установите Python и снова запустите файл.
pause
