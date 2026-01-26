from __future__ import annotations

from datetime import date

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QPlainTextEdit, QVBoxLayout, QWidget

from app import db


class DayView(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._current_date = date.today()
        layout = QVBoxLayout(self)
        self._header = QLabel()
        self._header.setAlignment(Qt.AlignLeft)
        self._editor = QPlainTextEdit()
        self._editor.setPlaceholderText("Дневные заметки...")
        layout.addWidget(self._header)
        layout.addWidget(self._editor)
        self.update_date(self._current_date)

    def update_date(self, date_obj: date) -> None:
        self._current_date = date_obj
        self._header.setText(date_obj.strftime("%A, %d %B %Y"))
        entry = db.fetch_note(date_obj.isoformat())
        self._editor.blockSignals(True)
        self._editor.setPlainText(entry.content if entry else "")
        self._editor.blockSignals(False)

    def save(self) -> None:
        db.upsert_note(self._current_date.isoformat(), self._editor.toPlainText())

    def collect_tasks(self) -> list[tuple[str, str]]:
        tasks: list[tuple[str, str]] = []
        for line in self._editor.toPlainText().splitlines():
            stripped = line.strip()
            if stripped.startswith("- ["):
                status = "done" if stripped[3:4].lower() == "x" else "undone"
                text = stripped[5:].strip()
                if text:
                    tasks.append((text, status))
        return tasks
