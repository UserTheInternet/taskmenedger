diff --git a/app/ui/main_window.py b/app/ui/main_window.py
index 67dbe568f86ef0f5feaf9187fc5e77c642289672..f082eb10122eee126dbd68c3e99bdd243c8ab176 100644
--- a/app/ui/main_window.py
+++ b/app/ui/main_window.py
@@ -1,111 +1,185 @@
 from __future__ import annotations
 
 import logging
 from datetime import date, timedelta
 from pathlib import Path
 
-from PySide6.QtCore import QDate, QTimer
-from PySide6.QtGui import QKeySequence, QAction
+from PySide6.QtCore import QDate, Qt, QTimer
+from PySide6.QtGui import QAction, QKeySequence, QShortcut
 from PySide6.QtWidgets import (
     QFileDialog,
+    QDialog,
     QMainWindow,
-    QShortcut,
     QTabWidget,
     QToolBar,
+    QToolButton,
+    QVBoxLayout,
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
+        self._apply_theme()
         self._week_view.set_week(self._current_week_start)
         self._day_view.update_date(date.today())
 
         self._autosave_timer = QTimer(self)
         self._autosave_timer.setInterval(5000)
         self._autosave_timer.timeout.connect(self.save_all)
         self._autosave_timer.start()
 
         self._bind_shortcuts()
 
     def _build_toolbar(self) -> None:
         toolbar = QToolBar("Навигация")
+        toolbar.setMovable(False)
         self.addToolBar(toolbar)
 
         prev_action = QAction("← Неделя", self)
         next_action = QAction("Неделя →", self)
         today_action = QAction("Сегодня", self)
         export_action = QAction("Экспорт недели", self)
         export_all_action = QAction("Экспорт JSON", self)
         import_action = QAction("Импорт JSON", self)
         backup_action = QAction("Резервная копия", self)
+        pomodoro_action = QAction("Помодоро", self)
+        pomodoro_action.triggered.connect(self._open_pomodoro_popup)
 
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
+        toolbar.addSeparator()
+
+        pomodoro_button = QToolButton(self)
+        pomodoro_button.setDefaultAction(pomodoro_action)
+        pomodoro_button.setText("🍅")
+        pomodoro_button.setToolTip("Помодоро")
+        pomodoro_button.setStyleSheet("font-size: 18px;")
+        toolbar.addWidget(pomodoro_button)
+
+    def _open_pomodoro_popup(self) -> None:
+        dialog = QDialog(self)
+        dialog.setWindowTitle("Помодоро")
+        dialog.setMinimumSize(420, 520)
+        dialog.setWindowModality(Qt.WindowModality.ApplicationModal)
+        layout = QVBoxLayout(dialog)
+        config = self._load_pomodoro_config()
+        popup_view = PomodoroView(config, enable_tray=False)
+        layout.addWidget(popup_view)
+        dialog.exec()
+
+    def _apply_theme(self) -> None:
+        self.setStyleSheet(
+            """
+            QMainWindow {
+                background-color: #f6f7fb;
+            }
+            QToolBar {
+                background: #ffffff;
+                border-bottom: 1px solid #e3e6ee;
+                spacing: 8px;
+                padding: 6px;
+            }
+            QToolButton, QPushButton {
+                background: #ffffff;
+                border: 1px solid #d7dbe7;
+                border-radius: 8px;
+                padding: 6px 12px;
+            }
+            QToolButton:hover, QPushButton:hover {
+                background: #f0f3fb;
+            }
+            QTabWidget::pane {
+                border: 1px solid #e3e6ee;
+                border-radius: 10px;
+                background: #ffffff;
+            }
+            QTabBar::tab {
+                background: #eef1f8;
+                border: 1px solid #d7dbe7;
+                border-radius: 8px;
+                padding: 6px 12px;
+                margin: 4px;
+            }
+            QTabBar::tab:selected {
+                background: #ffffff;
+                border: 1px solid #c9cfe0;
+            }
+            QLabel {
+                color: #1f2430;
+            }
+            QLineEdit, QListWidget, QSpinBox, QComboBox {
+                background: #ffffff;
+                border: 1px solid #d7dbe7;
+                border-radius: 8px;
+                padding: 6px;
+            }
+            """
+        )
 
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
