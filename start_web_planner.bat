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
if not exist "scripts\verify_web_bundle.py" if not exist "verify_web_bundle.py" set MISSING=1

if "%MISSING%"=="1" (
  echo.
  echo ОШИБКА: Папка неполная. Из-за этого появляются 404 на /css и /js.
  echo.
  echo Что сделать:
  echo 1) Скопируйте ВСЮ папку проекта целиком.
  echo 2) Запустите verify_web_bundle.bat (или python scripts\verify_web_bundle.py).
  echo 3) После COMPLETE снова запустите этот bat-файл.
  echo.
  pause
  exit /b 1
)

echo Запускаю локальный сервер для планировщика...
echo Адрес: http://127.0.0.1:8765/index.html
start "" "http://127.0.0.1:8765/index.html"

where py >nul 2>nul
if %ERRORLEVEL% EQU 0 (
  echo Использую: py -m http.server 8765
  py -m http.server 8765
  echo.
  echo Сервер остановлен или завершился с ошибкой. Нажмите любую клавишу.
  pause
  exit /b %ERRORLEVEL%
)

where python >nul 2>nul
if %ERRORLEVEL% EQU 0 (
  echo Использую: python -m http.server 8765
  python -m http.server 8765
  echo.
  echo Сервер остановлен или завершился с ошибкой. Нажмите любую клавишу.
  pause
  exit /b %ERRORLEVEL%
)

where python3 >nul 2>nul
if %ERRORLEVEL% EQU 0 (
  echo Использую: python3 -m http.server 8765
  python3 -m http.server 8765
  echo.
  echo Сервер остановлен или завершился с ошибкой. Нажмите любую клавишу.
  pause
  exit /b %ERRORLEVEL%
)

echo.
echo Не найден Python (py/python/python3) в PATH.
echo Установите Python и снова запустите файл.
pause
exit /b 1
