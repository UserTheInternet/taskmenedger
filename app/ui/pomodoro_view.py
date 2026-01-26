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
)

from app import db
from app.pomodoro import PomodoroConfig, PomodoroTimer


class PomodoroView(QWidget):
    def __init__(self, config: PomodoroConfig) -> None:
        super().__init__()
        self._config = config
        self._timer = PomodoroTimer(config)
        self._timer.tick.connect(self._update_timer)
        self._timer.session_complete.connect(self._handle_complete)
        self._tray = QSystemTrayIcon(self)
        self._tray.setIcon(QApplication.style().standardIcon(QApplication.style().SP_ComputerIcon))
        self._tray.setVisible(True)

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
        self._focus_minutes = QSpinBox()
        self._focus_minutes.setRange(5, 90)
        self._focus_minutes.setValue(self._config.focus_minutes)
        self._short_break = QSpinBox()
        self._short_break.setRange(1, 30)
        self._short_break.setValue(self._config.short_break_minutes)
        self._long_break = QSpinBox()
        self._long_break.setRange(5, 60)
        self._long_break.setValue(self._config.long_break_minutes)
        self._cycles = QSpinBox()
        self._cycles.setRange(2, 6)
        self._cycles.setValue(self._config.cycles_before_long_break)
        config_layout.addRow("Фокус (мин)", self._focus_minutes)
        config_layout.addRow("Перерыв (мин)", self._short_break)
        config_layout.addRow("Длинный перерыв", self._long_break)
        config_layout.addRow("Циклы", self._cycles)
        layout.addLayout(config_layout)

        self._save_config_button = QPushButton("Сохранить настройки")
        layout.addWidget(self._save_config_button)

        self._session_list = QListWidget()
        layout.addWidget(QLabel("Журнал сессий"))
        layout.addWidget(self._session_list)

        self._start_button.clicked.connect(self._start)
        self._pause_button.clicked.connect(self._timer.pause)
        self._reset_button.clicked.connect(self._timer.reset)
        self._save_config_button.clicked.connect(self._save_config)

        self.refresh_sessions()

    def _start(self) -> None:
        self._timer.configure_link(self._link_type.currentText(), self._link_id.text().strip() or None)
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
        self._tray.showMessage("Помодоро", message)
        self.refresh_sessions()

    def refresh_sessions(self) -> None:
        self._session_list.clear()
        for row in db.list_pomodoro_sessions(50):
            start_time = datetime.fromisoformat(row["start_time"]).strftime("%d.%m %H:%M")
            label = f"{start_time} • {row['duration'] // 60} мин • {row['linked_type']} {row['linked_id'] or ''}"
            self._session_list.addItem(label)
