from __future__ import annotations

import logging
from datetime import date, timedelta
from pathlib import Path

from PySide6.QtCore import QDate, QTimer
from PySide6.QtGui import QAction, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QFileDialog,
    QMainWindow,
    QTabWidget,
    QToolBar,
)

from app import db
from app.exporter import export_database_to_json, export_week_to_markdown, import_database_from_json
from app.pomodoro import PomodoroConfig
from app.ui.day_view import DayView
from app.ui.list_view import ListView
from app.ui.pomodoro_view import PomodoroView
from app.ui.week_view import WeekView

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Заметки/Планер + Помодоро")
        self.resize(1200, 720)
        self._current_week_start = WeekView.week_start_for(date.today())

        self._tabs = QTabWidget()
        self._week_view = WeekView()
        self._day_view = DayView()
        self._list_view = ListView()
        config = self._load_pomodoro_config()
        self._pomodoro_view = PomodoroView(config)

        self._tabs.addTab(self._week_view, "Неделя")
        self._tabs.addTab(self._day_view, "День")
        self._tabs.addTab(self._list_view, "Список")
        self._tabs.addTab(self._pomodoro_view, "Помодоро")
        self.setCentralWidget(self._tabs)

        self._build_toolbar()
        self._week_view.set_week(self._current_week_start)
        self._day_view.update_date(date.today())

        self._autosave_timer = QTimer(self)
        self._autosave_timer.setInterval(5000)
        self._autosave_timer.timeout.connect(self.save_all)
        self._autosave_timer.start()

        self._bind_shortcuts()

    def _build_toolbar(self) -> None:
        toolbar = QToolBar("Навигация")
        self.addToolBar(toolbar)

        prev_action = QAction("← Неделя", self)
        next_action = QAction("Неделя →", self)
        today_action = QAction("Сегодня", self)
        export_action = QAction("Экспорт недели", self)
        export_all_action = QAction("Экспорт JSON", self)
        import_action = QAction("Импорт JSON", self)
        backup_action = QAction("Резервная копия", self)

        prev_action.triggered.connect(self.prev_week)
        next_action.triggered.connect(self.next_week)
        today_action.triggered.connect(self.go_today)
        export_action.triggered.connect(self.export_week)
        export_all_action.triggered.connect(self.export_json)
        import_action.triggered.connect(self.import_json)
        backup_action.triggered.connect(self.backup_database)

        toolbar.addAction(prev_action)
        toolbar.addAction(next_action)
        toolbar.addAction(today_action)
        toolbar.addSeparator()
        toolbar.addAction(export_action)
        toolbar.addAction(export_all_action)
        toolbar.addAction(import_action)
        toolbar.addAction(backup_action)

    def _bind_shortcuts(self) -> None:
        QShortcut(QKeySequence("Ctrl+S"), self, activated=self.save_all)
        QShortcut(QKeySequence("Ctrl+F"), self, activated=self._focus_search)
        QShortcut(QKeySequence("Ctrl+Z"), self, activated=self._undo)
        QShortcut(QKeySequence("Ctrl+Enter"), self, activated=self._insert_newline)

    def _focus_search(self) -> None:
        self._tabs.setCurrentWidget(self._list_view)
        self._list_view.setFocus()

    def _undo(self) -> None:
        widget = self.focusWidget()
        if hasattr(widget, "undo"):
            widget.undo()

    def _insert_newline(self) -> None:
        widget = self.focusWidget()
        if hasattr(widget, "insertPlainText"):
            widget.insertPlainText("\n")

    def prev_week(self) -> None:
        self.save_all()
        self._current_week_start -= timedelta(days=7)
        self._week_view.set_week(self._current_week_start)

    def next_week(self) -> None:
        self.save_all()
        self._current_week_start += timedelta(days=7)
        self._week_view.set_week(self._current_week_start)

    def go_today(self) -> None:
        self.save_all()
        today = date.today()
        self._current_week_start = WeekView.week_start_for(today)
        self._week_view.set_week(self._current_week_start)
        self._day_view.update_date(today)

    def save_all(self) -> None:
        notes = self._week_view.collect_notes()
        for note_date, content in notes.items():
            db.upsert_note(note_date, content)
        tasks_by_date = self._week_view.extract_tasks()
        for note_date, tasks in tasks_by_date.items():
            db.replace_tasks_for_date(note_date, tasks)
        self._day_view.save()
        db.replace_tasks_for_date(
            self._day_view._current_date.isoformat(),
            self._day_view.collect_tasks(),
        )
        self._list_view.refresh()

    def export_week(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Экспорт недели",
            str(Path.home() / "week.md"),
            "Markdown (*.md)",
        )
        if path:
            export_week_to_markdown(self._current_week_start, Path(path))

    def export_json(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Экспорт базы",
            str(Path.home() / "planner.json"),
            "JSON (*.json)",
        )
        if path:
            export_database_to_json(Path(path))

    def import_json(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Импорт базы",
            str(Path.home()),
            "JSON (*.json)",
        )
        if path:
            import_database_from_json(Path(path))
            self.go_today()

    def backup_database(self) -> None:
        backup_path = db.backup_database()
        logger.info("Backup created at %s", backup_path)

    def closeEvent(self, event) -> None:  # type: ignore[override]
        self.save_all()
        super().closeEvent(event)

    def _load_pomodoro_config(self) -> PomodoroConfig:
        settings = db.get_setting(
            "pomodoro",
            {
                "focus": 25,
                "short_break": 5,
                "long_break": 15,
                "cycles": 4,
            },
        )
        return PomodoroConfig(
            focus_minutes=settings.get("focus", 25),
            short_break_minutes=settings.get("short_break", 5),
            long_break_minutes=settings.get("long_break", 15),
            cycles_before_long_break=settings.get("cycles", 4),
        )
