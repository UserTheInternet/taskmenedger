from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "dist" / "weekly-planner-pwa"

FILES = [
    ROOT / "index.html",
    ROOT / "manifest.webmanifest",
    ROOT / "sw.js",
    ROOT / "icon.svg",
    ROOT / "start_web_planner.bat",
]

DIRS = [
    ROOT / "css",
    ROOT / "js",
]

if OUT_DIR.exists():
    shutil.rmtree(OUT_DIR)
OUT_DIR.mkdir(parents=True, exist_ok=True)

for file_path in FILES:
    if not file_path.exists():
        raise FileNotFoundError(f"Не найден файл: {file_path}")
    shutil.copy2(file_path, OUT_DIR / file_path.name)

for dir_path in DIRS:
    if not dir_path.exists():
        raise FileNotFoundError(f"Не найдена папка: {dir_path}")
    shutil.copytree(dir_path, OUT_DIR / dir_path.name)

print(f"Готово: {OUT_DIR}")
