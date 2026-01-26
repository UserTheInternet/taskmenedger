$ErrorActionPreference = "Stop"

param(
    [string]$RepoPath = (Get-Location).Path,
    [string]$Branch = "main"
)

Write-Host "Переход в репозиторий: $RepoPath"
Set-Location $RepoPath

if (-not (Test-Path .git)) {
    Write-Error "Это не Git-репозиторий. Укажите путь через -RepoPath."
    exit 1
}

Write-Host "Получаю обновления..."
git fetch origin

Write-Host "Обновляю ветку $Branch..."
git checkout $Branch

git pull origin $Branch

Write-Host "Готово. При необходимости пересоберите setup: scripts\\build_installer.ps1"
