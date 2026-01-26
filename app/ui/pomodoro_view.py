diff --git a/app/ui/pomodoro_view.py b/app/ui/pomodoro_view.py
index 2f653d6b93c927a7eff3dd525dd3574c12ba40f2..4b3c5187ffdacc0589446fdcc006e51759711608 100644
--- a/app/ui/pomodoro_view.py
+++ b/app/ui/pomodoro_view.py
@@ -1,59 +1,64 @@
 from __future__ import annotations
 
 from datetime import datetime
 
 from PySide6.QtCore import Qt
 from PySide6.QtWidgets import (
     QComboBox,
     QFormLayout,
     QHBoxLayout,
     QLabel,
     QLineEdit,
     QListWidget,
     QPushButton,
     QSpinBox,
     QVBoxLayout,
     QWidget,
     QSystemTrayIcon,
     QApplication,
+    QStyle,
 )
 
 from app import db
 from app.pomodoro import PomodoroConfig, PomodoroTimer
 
 
 class PomodoroView(QWidget):
-    def __init__(self, config: PomodoroConfig) -> None:
+    def __init__(self, config: PomodoroConfig, *, enable_tray: bool = True) -> None:
         super().__init__()
         self._config = config
         self._timer = PomodoroTimer(config)
         self._timer.tick.connect(self._update_timer)
         self._timer.session_complete.connect(self._handle_complete)
-        self._tray = QSystemTrayIcon(self)
-        self._tray.setIcon(QApplication.style().standardIcon(QApplication.style().SP_ComputerIcon))
-        self._tray.setVisible(True)
+        self._tray: QSystemTrayIcon | None = None
+        if enable_tray:
+            self._tray = QSystemTrayIcon(self)
+            style = QApplication.style()
+            standard_icon = getattr(QStyle.StandardPixmap, "SP_ComputerIcon", QStyle.StandardPixmap.SP_DesktopIcon)
+            self._tray.setIcon(style.standardIcon(standard_icon))
+            self._tray.setVisible(True)
 
         layout = QVBoxLayout(self)
         self._timer_label = QLabel("25:00")
         self._timer_label.setAlignment(Qt.AlignCenter)
         self._timer_label.setStyleSheet("font-size: 32px;")
         layout.addWidget(self._timer_label)
 
         controls = QHBoxLayout()
         self._start_button = QPushButton("Старт")
         self._pause_button = QPushButton("Пауза")
         self._reset_button = QPushButton("Сброс")
         controls.addWidget(self._start_button)
         controls.addWidget(self._pause_button)
         controls.addWidget(self._reset_button)
         layout.addLayout(controls)
 
         link_layout = QFormLayout()
         self._link_type = QComboBox()
         self._link_type.addItems(["day", "task", "project"])
         self._link_id = QLineEdit()
         link_layout.addRow("Привязка:", self._link_type)
         link_layout.addRow("ID/тема:", self._link_id)
         layout.addLayout(link_layout)
 
         config_layout = QFormLayout()
@@ -94,34 +99,35 @@ class PomodoroView(QWidget):
         self._timer.start()
 
     def _save_config(self) -> None:
         self._config.focus_minutes = self._focus_minutes.value()
         self._config.short_break_minutes = self._short_break.value()
         self._config.long_break_minutes = self._long_break.value()
         self._config.cycles_before_long_break = self._cycles.value()
         db.set_setting(
             "pomodoro",
             {
                 "focus": self._config.focus_minutes,
                 "short_break": self._config.short_break_minutes,
                 "long_break": self._config.long_break_minutes,
                 "cycles": self._config.cycles_before_long_break,
             },
         )
         self._timer.reset()
 
     def _update_timer(self, seconds: int) -> None:
         minutes = seconds // 60
         secs = seconds % 60
         self._timer_label.setText(f"{minutes:02d}:{secs:02d}")
 
     def _handle_complete(self, mode: str) -> None:
         message = "Фокус завершён" if mode != "focus" else "Перерыв завершён"
-        self._tray.showMessage("Помодоро", message)
+        if self._tray:
+            self._tray.showMessage("Помодоро", message)
         self.refresh_sessions()
 
     def refresh_sessions(self) -> None:
         self._session_list.clear()
         for row in db.list_pomodoro_sessions(50):
             start_time = datetime.fromisoformat(row["start_time"]).strftime("%d.%m %H:%M")
             label = f"{start_time} • {row['duration'] // 60} мин • {row['linked_type']} {row['linked_id'] or ''}"
             self._session_list.addItem(label)
