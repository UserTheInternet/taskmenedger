@echo off
setlocal
cd /d "%~dp0"
chcp 65001 >nul

set VERIFY_SCRIPT=scripts\verify_web_bundle.py
if not exist "%VERIFY_SCRIPT%" set VERIFY_SCRIPT=verify_web_bundle.py

echo === Проверка комплекта файлов планировщика ===
echo Скрипт проверки: %VERIFY_SCRIPT%

if not exist "%VERIFY_SCRIPT%" (
  echo Не найден файл проверки: %VERIFY_SCRIPT%
  pause
  exit /b 1
)

where py >nul 2>nul
if %ERRORLEVEL% EQU 0 (
  py "%VERIFY_SCRIPT%"
  echo.
  if %ERRORLEVEL% EQU 0 (
    echo Проверка завершена: COMPLETE
  ) else (
    echo Проверка завершена: INCOMPLETE
  )
  pause
  exit /b %ERRORLEVEL%
)

where python >nul 2>nul
if %ERRORLEVEL% EQU 0 (
  python "%VERIFY_SCRIPT%"
  echo.
  if %ERRORLEVEL% EQU 0 (
    echo Проверка завершена: COMPLETE
  ) else (
    echo Проверка завершена: INCOMPLETE
  )
  pause
  exit /b %ERRORLEVEL%
)

where python3 >nul 2>nul
if %ERRORLEVEL% EQU 0 (
  python3 "%VERIFY_SCRIPT%"
  echo.
  if %ERRORLEVEL% EQU 0 (
    echo Проверка завершена: COMPLETE
  ) else (
    echo Проверка завершена: INCOMPLETE
  )
  pause
  exit /b %ERRORLEVEL%
)

echo Не найден Python (py/python/python3) в PATH.
echo Установите Python и повторите.
pause
exit /b 1
