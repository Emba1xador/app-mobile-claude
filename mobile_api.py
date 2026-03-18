from __future__ import annotations

from pathlib import Path

from services.mobile_api import main


if __name__ == "__main__":
    raise SystemExit(main(Path(__file__).resolve().parent))
