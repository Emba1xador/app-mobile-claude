from __future__ import annotations

import pytest
from PySide6.QtWidgets import QApplication

from ui.theme import APP_QSS, build_app_palette


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    app.setPalette(build_app_palette())
    app.setStyleSheet(APP_QSS)
    return app
