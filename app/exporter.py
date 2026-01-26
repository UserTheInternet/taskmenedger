from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from app import db


def export_week_to_markdown(start_date: date, target_path: Path) -> None:
    lines: list[str] = []
    for offset in range(7):
        current_date = start_date.fromordinal(start_date.toordinal() + offset)
        entry = db.fetch_note(current_date.isoformat())
        lines.append(f"## {current_date.strftime('%A %d.%m.%Y')}")
        lines.append(entry.content if entry else "")
        lines.append("")
    target_path.write_text("\n".join(lines), encoding="utf-8")


def export_database_to_json(target_path: Path) -> None:
    notes = [note.__dict__ for note in db.list_notes()]
    sessions = [dict(row) for row in db.list_pomodoro_sessions(1000)]
    data = {
        "notes": notes,
        "sessions": sessions,
    }
    target_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def import_database_from_json(source_path: Path) -> None:
    payload = json.loads(source_path.read_text(encoding="utf-8"))
    for note in payload.get("notes", []):
        db.upsert_note(note["date"], note.get("content", ""))
    for session in payload.get("sessions", []):
        db.add_pomodoro_session(
            start_time=session["start_time"],
            duration=session["duration"],
            break_duration=session["break_duration"],
            linked_type=session.get("linked_type", "day"),
            linked_id=session.get("linked_id"),
        )
