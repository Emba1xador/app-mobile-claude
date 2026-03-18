from __future__ import annotations

import json
import logging
from pathlib import Path

LOGGER = logging.getLogger(__name__)


class WhatsAppStore:
    def __init__(self, root: Path) -> None:
        self.path = root / "banca_whatsapp_map.json"

    def load(self) -> dict[str, str]:
        if not self.path.exists():
            return {}
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            LOGGER.warning("Falha ao carregar mapa de WhatsApp %s: %s", self.path, exc)
            return {}
        if not isinstance(payload, dict):
            LOGGER.warning("Mapa de WhatsApp inv\u00e1lido em %s; usando mapa vazio.", self.path)
            return {}
        return {str(key): str(value) for key, value in payload.items()}

    def save(self, mapping: dict[str, str]) -> None:
        self.path.write_text(
            json.dumps(mapping, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
