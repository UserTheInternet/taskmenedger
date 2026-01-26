from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from PySide6.QtCore import QObject, QTimer, Signal

from app import db


@dataclass
class PomodoroConfig:
    focus_minutes: int = 25
    short_break_minutes: int = 5
    long_break_minutes: int = 15
    cycles_before_long_break: int = 4


class PomodoroTimer(QObject):
    tick = Signal(int)
    session_complete = Signal(str)

    def __init__(self, config: PomodoroConfig) -> None:
        super().__init__()
        self.config = config
        self._timer = QTimer()
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._on_tick)
        self._remaining = self.config.focus_minutes * 60
        self._mode = "focus"
        self._cycles = 0
        self._running = False
        self._linked_type = "day"
        self._linked_id: str | None = None

    @property
    def mode(self) -> str:
        return self._mode

    @property
    def cycles(self) -> int:
        return self._cycles

    def configure_link(self, linked_type: str, linked_id: str | None) -> None:
        self._linked_type = linked_type
        self._linked_id = linked_id

    def start(self) -> None:
        if not self._running:
            self._running = True
            self._timer.start()

    def pause(self) -> None:
        if self._running:
            self._running = False
            self._timer.stop()

    def reset(self) -> None:
        self.pause()
        self._mode = "focus"
        self._remaining = self.config.focus_minutes * 60
        self.tick.emit(self._remaining)

    def _on_tick(self) -> None:
        if self._remaining <= 0:
            self._complete_session()
            return
        self._remaining -= 1
        self.tick.emit(self._remaining)

    def _complete_session(self) -> None:
        if self._mode == "focus":
            self._cycles += 1
            db.add_pomodoro_session(
                start_time=datetime.utcnow().isoformat(),
                duration=self.config.focus_minutes * 60,
                break_duration=self._break_duration() * 60,
                linked_type=self._linked_type,
                linked_id=self._linked_id,
            )
            if self._cycles % self.config.cycles_before_long_break == 0:
                self._mode = "long_break"
                self._remaining = self.config.long_break_minutes * 60
            else:
                self._mode = "short_break"
                self._remaining = self.config.short_break_minutes * 60
        else:
            self._mode = "focus"
            self._remaining = self.config.focus_minutes * 60
        self.tick.emit(self._remaining)
        self.session_complete.emit(self._mode)

    def _break_duration(self) -> int:
        if self._cycles % self.config.cycles_before_long_break == 0:
            return self.config.long_break_minutes
        return self.config.short_break_minutes
