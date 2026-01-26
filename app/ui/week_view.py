from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from PySide6.QtCore import Qt, QDate
from PySide6.QtWidgets import QGridLayout, QLabel, QPlainTextEdit, QWidget

from app import db


WEEKDAYS = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]


@dataclass
class DayCell:
    date: date
    editor: QPlainTextEdit
    header: QLabel


class WeekView(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._layout = QGridLayout(self)
        self._layout.setSpacing(8)
        self._cells: list[DayCell] = []
        self._build_headers()

    def _build_headers(self) -> None:
        for col, day_name in enumerate(WEEKDAYS):
            header = QLabel(day_name)
            header.setAlignment(Qt.AlignCenter)
            self._layout.addWidget(header, 0, col)
            editor = QPlainTextEdit()
            editor.setPlaceholderText("Введите заметки...")
            editor.setTabChangesFocus(False)
            self._layout.addWidget(editor, 1, col)
            self._cells.append(DayCell(date.today(), editor, header))

    def set_week(self, start_date: date) -> None:
        for offset, cell in enumerate(self._cells):
            current_date = start_date + timedelta(days=offset)
            cell.date = current_date
            cell.header.setText(f"{WEEKDAYS[offset]}\n{current_date.strftime('%d.%m')}")
            entry = db.fetch_note(current_date.isoformat())
            cell.editor.blockSignals(True)
            cell.editor.setPlainText(entry.content if entry else "")
            cell.editor.blockSignals(False)

    def collect_notes(self) -> dict[str, str]:
        data: dict[str, str] = {}
        for cell in self._cells:
            data[cell.date.isoformat()] = cell.editor.toPlainText()
        return data

    def focus_day(self, target_date: date) -> None:
        for cell in self._cells:
            if cell.date == target_date:
                cell.editor.setFocus()
                return

    def extract_tasks(self) -> dict[str, list[tuple[str, str]]]:
        tasks_by_date: dict[str, list[tuple[str, str]]] = {}
        for cell in self._cells:
            tasks: list[tuple[str, str]] = []
            for line in cell.editor.toPlainText().splitlines():
                stripped = line.strip()
                if stripped.startswith("- ["):
                    status = "done" if stripped[3:4].lower() == "x" else "undone"
                    text = stripped[5:].strip()
                    if text:
                        tasks.append((text, status))
            tasks_by_date[cell.date.isoformat()] = tasks
        return tasks_by_date

    @staticmethod
    def week_start_for(date_obj: date) -> date:
        return date_obj - timedelta(days=date_obj.weekday())

    @staticmethod
    def to_qdate(date_obj: date) -> QDate:
        return QDate(date_obj.year, date_obj.month, date_obj.day)

    @staticmethod
    def from_qdate(qdate: QDate) -> date:
        return date(qdate.year(), qdate.month(), qdate.day())
