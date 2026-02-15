from pathlib import Path

REQUIRED_FILES = [
    "index.html",
    "manifest.webmanifest",
    "sw.js",
    "icon.svg",
    "start_web_planner.bat",
    "css/styles.css",
    "js/app.js",
    "js/ui/render.js",
    "js/ui/events.js",
    "js/storage/vaultFs.js",
    "js/storage/vaultIndex.js",
    "js/utils/date.js",
    "js/utils/md.js",
]


def main() -> int:
    root = Path.cwd()
    missing = [rel for rel in REQUIRED_FILES if not (root / rel).exists()]

    print(f"Проверка папки: {root}")
    if not missing:
        print("COMPLETE: все обязательные файлы на месте.")
        return 0

    print("INCOMPLETE: отсутствуют файлы:")
    for rel in missing:
        print(f" - {rel}")

    print("\nСкопируйте всю папку dist/weekly-planner-pwa целиком.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
