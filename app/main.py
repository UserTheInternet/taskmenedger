import logging
from pathlib import Path

from PySide6.QtWidgets import QApplication

from app import db
from app.ui.main_window import MainWindow


def setup_logging() -> None:
    data_dir = db.get_data_dir()
    logs_dir = data_dir / "logs"
    logs_dir.mkdir(exist_ok=True)
    log_path = logs_dir / "app.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        handlers=[
            logging.FileHandler(log_path, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )


def main() -> None:
    setup_logging()
    db.init_db()
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()


if __name__ == "__main__":
    main()
