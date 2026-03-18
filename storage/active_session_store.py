from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import NamedTuple

from app_state.session import AppState
from storage.serializers import app_state_to_dict, dict_to_app_state

LOGGER = logging.getLogger(__name__)


class ActiveSessionToken(NamedTuple):
    mtime_ns: int
    size: int


class ActiveSessionStore:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.runtime_dir = self.root / "runtime"
        self.runtime_dir.mkdir(parents=True, exist_ok=True)
        self.path = self.runtime_dir / "active_session.json"

    def exists(self) -> bool:
        return self.path.exists()

    def save(self, state: AppState) -> Path:
        payload = json.dumps(app_state_to_dict(state), indent=2, ensure_ascii=False)
        temp_path = self.path.with_suffix(".tmp")
        temp_path.write_text(payload, encoding="utf-8")
        temp_path.replace(self.path)
        return self.path

    def clear(self) -> None:
        if not self.exists():
            return
        self.path.unlink()

    def load(self) -> AppState:
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
            return dict_to_app_state(payload)
        except (OSError, json.JSONDecodeError, KeyError, TypeError) as exc:
            LOGGER.warning("Falha ao carregar sessao ativa %s: %s", self.path, exc)
            raise ValueError("A sessao ativa esta corrompida, invalida ou incompativel.") from exc

    def try_load(self) -> AppState | None:
        if not self.exists():
            return None
        try:
            return self.load()
        except ValueError:
            return None

    def updated_at(self) -> datetime | None:
        if not self.exists():
            return None
        return datetime.fromtimestamp(self.path.stat().st_mtime).astimezone()

    def snapshot_token(self) -> ActiveSessionToken | None:
        if not self.exists():
            return None
        stat = self.path.stat()
        return ActiveSessionToken(mtime_ns=stat.st_mtime_ns, size=stat.st_size)
