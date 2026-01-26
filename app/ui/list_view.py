from __future__ import annotations

from datetime import date

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app import db


class ListView(QWidget):
    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        filters = QHBoxLayout()
        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("Поиск...")
        self._search_button = QPushButton("Найти")
        self._reset_button = QPushButton("Сброс")
        filters.addWidget(QLabel("Поиск:"))
        filters.addWidget(self._search_input)
        filters.addWidget(self._search_button)
        filters.addWidget(self._reset_button)
        layout.addLayout(filters)
        self._list = QListWidget()
        layout.addWidget(self._list)
        self._search_button.clicked.connect(self._perform_search)
        self._reset_button.clicked.connect(self.refresh)
        self._search_input.returnPressed.connect(self._perform_search)
        self.refresh()

    def refresh(self) -> None:
        self._list.clear()
        for entry in db.list_notes():
            self._list.addItem(self._format_entry(entry.date, entry.content))

    def _perform_search(self) -> None:
        query = self._search_input.text().strip()
        if not query:
            self.refresh()
            return
        self._list.clear()
        for entry in db.search_notes(query):
            self._list.addItem(self._format_entry(entry.date, entry.content))

    @staticmethod
    def _format_entry(entry_date: str, content: str) -> QListWidgetItem:
        preview = content.strip().replace("\n", " ")[:120]
        label = f"{entry_date} — {preview}"
        item = QListWidgetItem(label)
        item.setToolTip(content)
        item.setTextAlignment(Qt.AlignLeft)
        return item
