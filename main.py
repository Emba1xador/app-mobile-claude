from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

from services.mobile_backend_manager import MobileBackendManager
from services.controller import BancaController
from ui.main_window import MainWindow
from ui.theme import APP_QSS, build_app_palette


def configure_logging() -> None:
    level = logging.DEBUG if os.getenv("BANCA_DEBUG") == "1" else logging.WARNING
    logging.basicConfig(level=level, format="%(levelname)s %(name)s: %(message)s")


def main() -> int:
    configure_logging()
    root = Path(__file__).resolve().parent
    app = QApplication(sys.argv)
    app.setApplicationName("BANCA APP 2.0")
    app_font = app.font()
    app_font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
    app_font.setHintingPreference(QFont.HintingPreference.PreferFullHinting)
    app.setFont(app_font)
    app.setPalette(build_app_palette())
    app.setStyleSheet(APP_QSS)

    controller = BancaController(root, restore_active_session=False)
    mobile_backend_manager = MobileBackendManager(root, host="0.0.0.0", port=8765)
    window = MainWindow(controller, root, mobile_backend_manager=mobile_backend_manager)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
