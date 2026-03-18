from __future__ import annotations

import json
from datetime import datetime
import logging
from pathlib import Path

from app_state.session import AppState
from storage.serializers import app_state_to_dict, dict_to_app_state

LOGGER = logging.getLogger(__name__)


class JsonStore:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.saves_dir = self.root / "saves"
        self.saves_dir.mkdir(parents=True, exist_ok=True)

    def save(self, state: AppState, path: Path | None = None) -> Path:
        target = path or self.saves_dir / f"banca_save_{datetime.now():%Y%m%d_%H%M%S_%f}.json"
        target.write_text(
            json.dumps(app_state_to_dict(state), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return target

    def load(self, path: Path) -> AppState:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            return dict_to_app_state(payload)
        except (OSError, json.JSONDecodeError, KeyError, TypeError) as exc:
            LOGGER.warning("Falha ao carregar save %s: %s", path, exc)
            raise ValueError("O arquivo selecionado est\u00e1 corrompido, inv\u00e1lido ou incompat\u00edvel.") from exc
