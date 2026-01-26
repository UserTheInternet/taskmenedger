$ErrorActionPreference = "Stop"

Write-Host "[1/3] Создание venv и установка зависимостей"
python -m venv .venv
. .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install pyinstaller

Write-Host "[2/3] Сборка exe"
pyinstaller --noconfirm --onefile --windowed --name Taskmenedger app/main.py

Write-Host "[3/3] Сборка установщика Inno Setup"
# Требуется установленный Inno Setup 6 и доступный iscc.exe в PATH
iscc installer\Taskmenedger.iss

Write-Host "Готово: dist\Taskmenedger.exe и installer\Output\Taskmenedger-Setup.exe"
