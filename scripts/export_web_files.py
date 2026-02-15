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

HELPER_SCRIPTS = [
    ROOT / "scripts" / "verify_web_bundle.py",
]

REQUIRED_RELATIVE_PATHS = [
    "index.html",
    "manifest.webmanifest",
    "sw.js",
    "icon.svg",
    "start_web_planner.bat",
    "verify_web_bundle.py",
    "css/styles.css",
    "js/app.js",
    "js/ui/render.js",
    "js/ui/events.js",
    "js/storage/vaultFs.js",
    "js/storage/vaultIndex.js",
    "js/utils/date.js",
    "js/utils/md.js",
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

for helper in HELPER_SCRIPTS:
    if not helper.exists():
        raise FileNotFoundError(f"Не найден helper-скрипт: {helper}")
    shutil.copy2(helper, OUT_DIR / helper.name)

required_list_file = OUT_DIR / "REQUIRED_FILES.txt"
required_list_file.write_text("\n".join(REQUIRED_RELATIVE_PATHS) + "\n", encoding="utf-8")

print(f"Готово: {OUT_DIR}")
print("\nПроверка комплекта:")
missing = []
for rel in REQUIRED_RELATIVE_PATHS:
    exists = (OUT_DIR / rel).exists()
    print(f" {'OK' if exists else 'MISSING'}  {rel}")
    if not exists:
        missing.append(rel)

if missing:
    raise SystemExit("\nСборка неполная. Исправьте missing-файлы выше.")

print("\nМожно копировать папку dist/weekly-planner-pwa на Рабочий стол целиком.")
