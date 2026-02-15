@echo off
setlocal
cd /d "%~dp0"

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

echo.
echo Не найден Python (py/python) в PATH.
echo Установите Python или откройте index.html напрямую двойным кликом.
pause
