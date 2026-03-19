from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPalette

from core.enums import BetType, Flag

# ── Conferix Light — warm sand/beige base, amber accent, dark text ──

COLOR_TOKENS = {
    # ── Surfaces — warm sand/beige ──
    "window_bg": "#E8E0D4",
    "panel_bg": "#F0E8DC",
    "surface_bg": "#DED6CA",
    "surface_alt": "#D4CCC0",
    "field_bg": "#F6F0E6",
    "field_hover": "#EDE6DA",
    "field_focus": "#F6F0E6",
    "toolbar_bg": "#F0E8DC",
    "footer_bg": "#F0E8DC",
    # ── Borders — warm, visible ──
    "border": "#A89C88",
    "divider": "#C0B8A4",
    # ── Text — dark warm ──
    "title": "#1C1810",
    "text": "#3A3428",
    "text_muted": "#7A7264",
    "text_subtle": "#A09888",
    "placeholder": "#B0A898",
    # ── Interaction — amber accent ──
    "hover": "#D8D0C4",
    "pressed": "#CCC4B8",
    "focus": "#C07818",
    "focus_strong": "#A86810",
    "selection": "#F0D8A8",
    "accent": "#C07818",
    "accent_hover": "#A86810",
    "accent_soft": "#F0D8A8",
    # ── Semantic ──
    "success_fg": "#1A5C2C",
    "success_bg": "#D4F0DC",
    "success_detail": "#1A8C3C",
    "warning_fg": "#6C4808",
    "warning_bg": "#FCF0C8",
    "warning_soft_bg": "#FDF6DC",
    "warning_detail": "#A87C10",
    "danger_fg": "#8C1C20",
    "danger_bg": "#FCE0DC",
    "danger_soft_bg": "#FDE8E4",
    "danger_detail": "#CC3838",
    "info_fg": "#1C3870",
    "info_bg": "#D8E8FC",
    # ── Manual entry ──
    "manual_bg": "#E8DCC8",
    "manual_border": "#B8A880",
    "manual_fg": "#1C1810",
    "manual_placeholder": "#8C8068",
    # ── Result panel ──
    "result_card_bg": "#DED6CA",
    "result_card_border": "#D4CCBC",
    "result_prize": "#7A7264",
    "result_value": "#1C1810",
    "result_group": "#A09888",
    # ── Summary ──
    "summary_section_bg": "#DED6CA",
    "summary_positive_bg": "#D4F0DC",
    "summary_positive_fg": "#1A5C2C",
    "summary_negative_bg": "#DED6CA",
    "summary_negative_fg": "#3A3428",
    "summary_detail": "#7A7264",
    # ── Pending panel ──
    "pending_panel_bg": "#F0E8DC",
    "pending_section_bg": "#FCF0C8",
    "pending_section_fg": "#6C4808",
    "pending_item_bg": "#DED6CA",
    "pending_item_fg": "#3A3428",
    # ── Finance ──
    "finance_header_bg": "#E8E0D4",
    "finance_contact_bg": "#DED6CA",
    "finance_row_even": "#F0E8DC",
    "finance_row_odd": "#E8E0D4",
    "finance_pending_even": "#E8E0D4",
    "finance_pending_odd": "#DED6CA",
    "finance_winner_even": "#D8F0DC",
    "finance_winner_odd": "#D0ECD4",
    "finance_received_bg": "#F6F0E6",
    "finance_received_missing_bg": "#E8E0D4",
    "finance_received_text": "#3A3428",
    "finance_received_missing_text": "#A09888",
    # ── Bet rows ──
    "winner_row": "#D4F0DC",
    "error_row": "#FCE0DC",
    "page_header_text": "#1C1810",
    "page_total_text": "#3A3428",
    "bet_text": "#3A3428",
    "empty_text": "#A09888",
    # ── Type badges — white text on vivid solid fills ──
    "badge_centena_fg": "#FFFFFF",
    "badge_centena_bg": "#3080B8",
    "badge_milhar_fg": "#FFFFFF",
    "badge_milhar_bg": "#208848",
    "badge_mc_fg": "#FFFFFF",
    "badge_mc_bg": "#7040A8",
    "badge_dezena_fg": "#FFFFFF",
    "badge_dezena_bg": "#B88020",
    "badge_duque_fg": "#FFFFFF",
    "badge_duque_bg": "#B86028",
    "badge_terno_fg": "#FFFFFF",
    "badge_terno_bg": "#B83838",
    "badge_grupo_fg": "#FFFFFF",
    "badge_grupo_bg": "#508818",
    "badge_terno_grupo_fg": "#FFFFFF",
    "badge_terno_grupo_bg": "#188080",
    "badge_fechamento_fg": "#FFFFFF",
    "badge_fechamento_bg": "#4060B0",
    # ── Flag badges ──
    "flag_invertida_fg": "#FFFFFF",
    "flag_invertida_bg": "#6040A0",
    "flag_de_fg": "#FFFFFF",
    "flag_de_bg": "#A87818",
    "flag_dem_fg": "#FFFFFF",
    "flag_dem_bg": "#B83050",
}

BLOCK_PALETTES = {
    False: {
        "page_header": QColor(0, 0, 0, 22),
        "page_total": QColor(0, 0, 0, 16),
        "row_light": QColor(0, 0, 0, 8),
        "row_dark": QColor(0, 0, 0, 5),
        "empty": QColor(0, 0, 0, 3),
    },
    True: {
        "page_header": QColor(0, 0, 0, 32),
        "page_total": QColor(0, 0, 0, 22),
        "row_light": QColor(0, 0, 0, 16),
        "row_dark": QColor(0, 0, 0, 11),
        "empty": QColor(0, 0, 0, 5),
    },
}


def color(name: str) -> QColor:
    return QColor(COLOR_TOKENS[name])


def with_alpha(name: str, alpha: int) -> QColor:
    value = color(name)
    value.setAlpha(alpha)
    return value


def tinted(color_name: str, alpha: int) -> QColor:
    return with_alpha(color_name, alpha)


SELECTION_FILL = QColor(192, 120, 24, 40)
WINNER_FILL = QColor(26, 140, 60, 35)
ERROR_FILL = QColor(204, 56, 56, 30)

TYPE_COLORS = {
    BetType.CENTENA: (color("badge_centena_fg"), color("badge_centena_bg")),
    BetType.MILHAR: (color("badge_milhar_fg"), color("badge_milhar_bg")),
    BetType.MILHAR_CENTENA: (color("badge_mc_fg"), color("badge_mc_bg")),
    BetType.DEZENA: (color("badge_dezena_fg"), color("badge_dezena_bg")),
    BetType.DUQUE_DEZENA: (color("badge_duque_fg"), color("badge_duque_bg")),
    BetType.TERNO_DEZENA: (color("badge_terno_fg"), color("badge_terno_bg")),
    BetType.GRUPO: (color("badge_grupo_fg"), color("badge_grupo_bg")),
    BetType.TERNO_GRUPO: (color("badge_terno_grupo_fg"), color("badge_terno_grupo_bg")),
    BetType.FECHAMENTO: (color("badge_fechamento_fg"), color("badge_fechamento_bg")),
}

FLAG_COLORS = {
    Flag.INVERTIDA: (color("flag_invertida_fg"), color("flag_invertida_bg")),
    Flag.DE: (color("flag_de_fg"), color("flag_de_bg")),
    Flag.DEM: (color("flag_dem_fg"), color("flag_dem_bg")),
}

STATUS_COLORS = {
    "positive": (color("success_fg"), color("success_bg")),
    "warning": (color("warning_fg"), color("warning_bg")),
    "negative": (color("danger_fg"), color("danger_bg")),
}

ACTION_COLORS = {
    "default": color("text_subtle"),
    "available": color("success_detail"),
    "missing": color("danger_detail"),
    "config": color("warning_fg"),
    "send": color("focus_strong"),
}

QSS_COLORS = {
    **COLOR_TOKENS,
    "selection_rgba": "rgba(192, 120, 24, 60)",
}


APP_QSS = """
/* ═══════════════════════════════════════════════════
   Conferix — Light Theme
   Warm sand/beige, amber accent, dark text
   ═══════════════════════════════════════════════════ */

/* ── Global ── */

QMainWindow {{
    background: {window_bg};
}}

QWidget {{
    color: {text};
    background: {window_bg};
    font-family: "Segoe UI Variable Text", "Segoe UI";
    font-size: 11.0pt;
    selection-background-color: {selection};
    selection-color: {title};
}}

QWidget#middlePanel {{
    background: transparent;
    padding: 0 4px;
}}

QScrollArea > QWidget > QWidget,
QGroupBox > QWidget,
QSplitter > QWidget > QWidget {{
    background: transparent;
}}

/* ── Toolbar ── */

QToolBar#mainToolbar {{
    background: {panel_bg};
    border: none;
    border-bottom: 1px solid {border};
    border-radius: 0;
    spacing: 6px;
    padding: 8px 16px;
    margin: 0;
}}

QToolBar#mainToolbar::separator {{
    width: 1px;
    margin: 6px 4px;
    background: {divider};
}}

QToolBar#mainToolbar QToolButton {{
    min-height: 30px;
    padding: 4px 14px;
    border-radius: 6px;
    font-size: 9.4pt;
    font-weight: 700;
}}

QToolBar#mainToolbar QToolButton[toolbarTone="menu"] {{
    background: {surface_bg};
    border: none;
    color: {text};
    padding-right: 18px;
}}

QToolBar#mainToolbar QToolButton[toolbarTone="menu"]:hover {{
    background: {surface_alt};
}}

QToolBar#mainToolbar QToolButton[toolbarTone="quiet"] {{
    background: transparent;
    border: none;
    color: {text_muted};
}}

QToolBar#mainToolbar QToolButton[toolbarTone="quiet"]:hover {{
    background: {surface_bg};
    color: {text};
}}

QToolBar#mainToolbar QToolButton[toolbarTone="primary"] {{
    background: {accent_soft};
    border: none;
    color: {focus_strong};
}}

QToolBar#mainToolbar QToolButton[toolbarTone="primary"]:hover {{
    background: {accent};
    color: {title};
}}

QToolBar#mainToolbar QToolButton[toolbarTone="accent"] {{
    background: {accent};
    border: none;
    color: #FFFFFF;
    font-weight: 700;
}}

QToolBar#mainToolbar QToolButton[toolbarTone="accent"]:hover {{
    background: {accent_hover};
}}

QToolBar#mainToolbar QToolButton::menu-indicator {{
    subcontrol-origin: padding;
    subcontrol-position: right center;
    right: 8px;
}}

/* ── Labels ── */

QLabel[topTitle="true"] {{
    font-size: 15.0pt;
    font-weight: 760;
    color: {title};
}}

QLabel[toolbarLabel="true"] {{
    color: {text_muted};
    font-size: 8.5pt;
    font-weight: 650;
    padding-right: 4px;
}}

QLabel[toolbarMeta="true"] {{
    color: {text_subtle};
    font-size: 8.5pt;
    font-weight: 600;
}}

/* ── Generic buttons ── */

QToolButton,
QPushButton {{
    background: {surface_bg};
    color: {text};
    border: none;
    border-radius: 8px;
    min-height: 26px;
    padding: 4px 12px;
    font-weight: 600;
}}

QToolButton:hover,
QPushButton:hover {{
    background: {surface_alt};
    color: {title};
}}

QToolButton:pressed,
QPushButton:pressed {{
    background: {pressed};
}}

QToolButton:disabled,
QPushButton:disabled {{
    background: {panel_bg};
    color: {text_subtle};
}}

QDialogButtonBox QPushButton {{
    min-height: 28px;
    min-width: 92px;
}}

/* ── GroupBox / Panels ── */

QGroupBox {{
    font-size: 9.0pt;
    font-weight: 800;
    color: {text_muted};
    background: transparent;
    border: none;
    border-radius: 0;
    margin-top: 18px;
    padding-top: 4px;
    letter-spacing: 1px;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 4px;
    font-size: 9.0pt;
    font-weight: 800;
    color: {text_muted};
    text-transform: uppercase;
}}

QGroupBox#launchPanel,
QGroupBox#financePanel {{
    background: {panel_bg};
    border: 1px solid {border};
    border-radius: 10px;
}}

QGroupBox#resultPanel,
QGroupBox#sessionOverviewPanel,
QGroupBox#pendingPanel {{
    background: transparent;
}}

QGroupBox#financeTotalsPanel {{
    background: transparent;
    margin-top: 6px;
}}

/* ── Tables ── */

QTableView {{
    background: transparent;
    alternate-background-color: transparent;
    border: none;
    border-radius: 8px;
    gridline-color: transparent;
    selection-background-color: {selection_rgba};
    selection-color: {title};
    outline: 0;
}}

QTableView::item {{
    background: transparent;
}}

QTableView#betsTable {{
    background: transparent;
    border: none;
    border-radius: 0;
    selection-background-color: transparent;
}}

QTableView#betsTable::item {{
    border: none;
    padding: 0;
}}

QHeaderView::section,
QTableCornerButton::section {{
    background: {surface_bg};
    color: {text_muted};
    padding: 5px 10px;
    border: none;
    border-bottom: 1px solid {border};
    font-weight: 700;
}}

/* ── Form fields ── */

QLineEdit,
QTextEdit,
QPlainTextEdit,
QComboBox,
QAbstractSpinBox {{
    background: {field_bg};
    color: {text};
    border: 1px solid transparent;
    border-radius: 8px;
    padding: 6px 9px;
    selection-background-color: {selection};
    selection-color: {title};
    placeholder-text-color: {placeholder};
}}

QLineEdit:hover,
QTextEdit:hover,
QPlainTextEdit:hover,
QComboBox:hover,
QAbstractSpinBox:hover {{
    background: {field_hover};
    border-color: {divider};
}}

QLineEdit:focus,
QTextEdit:focus,
QPlainTextEdit:focus,
QComboBox:focus,
QAbstractSpinBox:focus,
QTableView:focus {{
    border: 1px solid {focus};
    background: {field_focus};
}}

QLineEdit:disabled,
QTextEdit:disabled,
QPlainTextEdit:disabled,
QComboBox:disabled,
QAbstractSpinBox:disabled {{
    background: {panel_bg};
    color: {text_subtle};
}}

QComboBox {{
    min-height: 26px;
    padding-right: 28px;
}}

QComboBox::drop-down {{
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 24px;
    border: none;
    background: {surface_bg};
    border-top-right-radius: 10px;
    border-bottom-right-radius: 10px;
}}

QComboBox QAbstractItemView,
QMenu,
QFileDialog QListView,
QFileDialog QTreeView {{
    background: {panel_bg};
    color: {text};
    border: 1px solid {border};
    border-radius: 8px;
    selection-background-color: {selection};
    selection-color: {title};
    outline: 0;
}}

QAbstractSpinBox::up-button,
QAbstractSpinBox::down-button {{
    width: 18px;
    background: {surface_bg};
    border: none;
}}

QAbstractSpinBox::up-button:hover,
QAbstractSpinBox::down-button:hover {{
    background: {surface_alt};
}}

/* ── Search widget ── */

QWidget#toolbarSearchWidget {{
    background: transparent;
    border: none;
    border-radius: 0;
    padding: 0;
}}

QComboBox#toolbarBlockSearch {{
    min-height: 34px;
    min-width: 180px;
    padding: 5px 36px 5px 12px;
    background: {field_bg};
    border: 1px solid transparent;
    border-radius: 8px;
    color: {title};
    font-size: 10.0pt;
    font-weight: 700;
}}

QComboBox#toolbarBlockSearch:hover {{
    background: {field_hover};
    border-color: {divider};
}}

QComboBox#toolbarBlockSearch:focus {{
    background: {field_focus};
    border: 1px solid {focus};
}}

QComboBox#toolbarBlockSearch::drop-down {{
    width: 28px;
    border: none;
    background: {surface_bg};
    border-top-right-radius: 10px;
    border-bottom-right-radius: 10px;
}}

QComboBox#toolbarBlockSearch QLineEdit {{
    background: transparent;
    border: none;
    padding: 0;
    color: {title};
}}

QComboBox#toolbarBlockSearch QAbstractItemView {{
    background: {panel_bg};
    border: 1px solid {border};
    selection-background-color: {selection};
    selection-color: {title};
}}

QToolButton#toolbarSearchClear {{
    min-width: 24px;
    max-width: 24px;
    min-height: 24px;
    max-height: 24px;
    padding: 0;
    border-radius: 8px;
    background: transparent;
    border: none;
    color: {text_muted};
    font-size: 10.5pt;
    font-weight: 700;
}}

QToolButton#toolbarSearchClear:hover {{
    background: {surface_bg};
    color: {title};
}}

/* ── Launch filters ── */

QWidget#launchFiltersBar {{
    background: {window_bg};
    border: none;
    border-radius: 8px;
    padding: 3px 4px;
}}

QToolButton[launchFilter="true"],
QToolButton[launchCompact="true"] {{
    min-height: 28px;
    padding: 4px 12px;
    border-radius: 8px;
    background: transparent;
    border: none;
    color: {text_muted};
    font-size: 9.1pt;
    font-weight: 700;
}}

QToolButton[launchFilter="true"]:hover,
QToolButton[launchCompact="true"]:hover {{
    background: {surface_bg};
    color: {text};
}}

QToolButton[launchFilter="true"]:checked,
QToolButton[launchCompact="true"]:checked {{
    background: {surface_bg};
    color: {title};
}}

/* ── Scrollbars ── */

QAbstractScrollArea,
QScrollArea {{
    border: none;
}}

QScrollBar:vertical {{
    background: transparent;
    width: 8px;
    margin: 4px 1px 4px 1px;
}}

QScrollBar::handle:vertical {{
    background: {border};
    min-height: 24px;
    border-radius: 4px;
}}

QScrollBar::handle:vertical:hover {{
    background: {text_subtle};
}}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical,
QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical {{
    background: none;
    border: none;
}}

QScrollBar:horizontal {{
    background: transparent;
    height: 8px;
    margin: 1px 4px 1px 4px;
}}

QScrollBar::handle:horizontal {{
    background: {border};
    min-width: 24px;
    border-radius: 4px;
}}

QScrollBar::handle:horizontal:hover {{
    background: {text_subtle};
}}

QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal,
QScrollBar::add-page:horizontal,
QScrollBar::sub-page:horizontal {{
    background: none;
    border: none;
}}

/* ── Splitter ── */

QSplitter::handle {{
    background: {divider};
    margin: 16px 2px;
    border-radius: 1px;
    max-width: 1px;
}}

QSplitter::handle:hover {{
    background: {accent};
    max-width: 2px;
}}

/* ── Status bar ── */

QStatusBar {{
    background: transparent;
    border: none;
    min-height: 50px;
}}

QStatusBar::item {{
    border: none;
}}

/* ── Summary panel ── */

QWidget[summaryRow="true"][summaryKind="section"] {{
    background: {surface_bg};
    border: none;
    border-radius: 8px;
}}

/* ── Session overview ── */

QToolButton[overviewTab="true"] {{
    min-height: 28px;
    padding: 4px 16px;
    border-radius: 6px;
    background: transparent;
    border: 1px solid {divider};
    color: {text_muted};
    font-size: 9.2pt;
    font-weight: 700;
}}

QToolButton[overviewTab="true"]:checked {{
    background: {surface_bg};
    border: 1px solid {border};
    color: {title};
}}

QToolButton[overviewTab="true"]:hover {{
    background: {surface_bg};
    color: {text};
}}

QWidget[overviewDetailRow="true"] {{
    background: {surface_bg};
    border: none;
    border-radius: 8px;
}}

QLabel[overviewDetailBet="true"] {{
    color: {title};
    font-size: 9.35pt;
    font-weight: 720;
}}

QLabel[overviewDetailMeta="true"] {{
    color: {text_muted};
    font-size: 8.45pt;
    font-weight: 620;
}}

QLabel[overviewDetailPrize="true"] {{
    color: {success_detail};
    font-size: 8.6pt;
    font-weight: 700;
}}

QLabel[overviewEmpty="true"] {{
    color: {text_subtle};
    font-size: 10.0pt;
    background: {surface_bg};
    border: none;
    border-radius: 8px;
    padding: 14px;
}}

/* ── Pendency panel ── */

QWidget[pendencyDetails="true"] {{
    background: transparent;
    border: none;
}}

QLabel[pendencyDetail="true"] {{
    color: {warning_detail};
    line-height: 1.4;
    font-size: 9.0pt;
    font-weight: 600;
    padding: 2px 0;
}}

QLabel[pendencyDetail="true"][pendencyTone="warning"] {{
    color: {text_muted};
}}

QLabel[pendencyEmpty="true"] {{
    color: {text_subtle};
    font-size: 10.0pt;
    border: none;
    border-radius: 8px;
    background: {surface_bg};
    padding: 14px;
}}

/* ── Finance table ── */

QTableView#financeTable {{
    background: transparent;
    border: none;
    border-radius: 8px;
    padding: 4px 0 4px 0;
    selection-background-color: transparent;
}}

QTableView#financeTable::item {{
    padding: 0 10px;
    border: none;
}}

QTableView#financeTable:focus {{
    border: 1px solid {focus};
}}

/* ── Finance totals panel ── */

QWidget[totalsMetricsGroup="true"] {{
    background: {surface_bg};
    border: none;
    border-radius: 8px;
}}

QWidget[totalsMetricRow="true"] {{
    background: transparent;
    border: none;
    border-radius: 0;
    padding: 7px 12px;
}}

QLabel[totalsMetricLabel="true"] {{
    color: {text_muted};
    font-weight: 620;
    font-size: 8.7pt;
}}

QLabel[totalsMetricValue="true"] {{
    color: {title};
    font-weight: 760;
    font-size: 12.3pt;
}}

QLineEdit[totalsPaidInput="true"] {{
    background: {field_bg};
    border: 1px solid transparent;
    border-radius: 8px;
    padding: 6px 10px;
    color: {title};
    font-weight: 740;
}}

QGroupBox#financeTotalsPanel QLineEdit {{
    background: {field_bg};
    border: 1px solid transparent;
    border-radius: 8px;
    min-height: 32px;
}}

QGroupBox#financeTotalsPanel QLineEdit:focus {{
    border: 1px solid {focus};
}}

QFrame#financeTotalsDivider {{
    color: {border};
    background: {border};
    min-height: 1px;
    max-height: 1px;
    margin: 2px 8px 4px 8px;
}}

QWidget[totalsBalanceCard="true"] {{
    background: {surface_bg};
    border: none;
    border-radius: 8px;
    max-height: 66px;
}}

QLabel[totalsBalanceLabel="true"] {{
    color: {text_muted};
    font-weight: 700;
    font-size: 8.4pt;
}}

QGroupBox#financeTotalsPanel QLabel[totalsResult="true"] {{
    font-size: 17.0pt;
    font-weight: 800;
    qproperty-alignment: AlignRight;
}}

QGroupBox#financeTotalsPanel QLabel[totalsResult="true"][cashTone="positive"] {{
    color: {success_detail};
}}

QGroupBox#financeTotalsPanel QLabel[totalsResult="true"][cashTone="negative"] {{
    color: {danger_detail};
}}

QGroupBox#financeTotalsPanel QLabel[totalsResult="true"][cashTone="neutral"] {{
    color: {text_muted};
}}

QGroupBox#financeTotalsPanel QLabel[totalsAccentLabel="true"] {{
    color: {title};
    font-weight: 700;
}}

QGroupBox#financeTotalsPanel QLabel[totalsLabel="true"] {{
    color: {text_muted};
    font-weight: 600;
    font-size: 8.6pt;
}}

QWidget[totalsNotesGroup="true"] {{
    background: transparent;
}}

QPlainTextEdit#sessionNotes {{
    background: {field_bg};
    border: 1px solid transparent;
    color: {text};
    border-radius: 8px;
    padding: 9px 10px;
    placeholder-text-color: {placeholder};
}}

QPlainTextEdit#sessionNotes:focus {{
    border: 1px solid {focus};
}}

/* ── Bottom bar ── */

QWidget#bottomBar {{
    background: {window_bg};
    border: none;
    border-top: 1px solid {border};
    border-radius: 0;
    padding: 2px 6px;
}}

QWidget[bottomZone="context"] {{
    background: {surface_bg};
    border: none;
    border-radius: 8px;
    padding: 0 10px;
}}

QWidget[bottomZone="metrics"],
QWidget[bottomZone="shortcuts"],
QWidget[bottomSegment="true"],
QWidget[bottomMetricsGroup="true"] {{
    background: transparent;
}}

QLabel[bottomContext="true"] {{
    color: {title};
    font-weight: 760;
    font-size: 10.6pt;
}}

QLabel[bottomInlineLabel="true"] {{
    color: {text_muted};
    font-weight: 620;
    font-size: 8.25pt;
}}

QLabel[bottomInlineValue="true"] {{
    color: {text};
    font-weight: 640;
    font-size: 9.45pt;
}}

QLabel[bottomInlineValueStrong="true"] {{
    color: {title};
    font-weight: 780;
    font-size: 12.0pt;
}}

QLabel[bottomInlineValueStrong="true"][saldoTone="positive"] {{
    color: {success_detail};
}}

QLabel[bottomInlineValueStrong="true"][saldoTone="negative"] {{
    color: {danger_detail};
}}

QLabel[bottomInlineValueStrong="true"][saldoTone="neutral"] {{
    color: {text_muted};
}}

QComboBox#bottomBlockSelector {{
    background: {field_bg};
    border: 1px solid transparent;
    min-height: 30px;
    padding: 3px 30px 3px 12px;
    font-weight: 700;
    border-radius: 8px;
    color: {text};
}}

QComboBox#bottomBlockSelector::drop-down {{
    width: 22px;
    border: none;
}}

QComboBox#bottomBlockSelector:hover,
QComboBox#bottomBlockSelector:focus {{
    background: {field_hover};
    border-color: {divider};
    color: {title};
}}

QFrame[bottomSeparator="true"] {{
    color: transparent;
    background: transparent;
    min-width: 0;
    max-width: 0;
}}

QLabel[bottomHint="true"] {{
    color: {text_subtle};
    font-size: 8.0pt;
    font-weight: 560;
}}

/* ── Dialogs, menus, tooltips ── */

QDialog,
QMessageBox,
QFileDialog {{
    background: {panel_bg};
}}

QDialog QLabel,
QMessageBox QLabel,
QFileDialog QLabel {{
    color: {text};
}}

QMenu {{
    background: {panel_bg};
    border: 1px solid {border};
    border-radius: 8px;
    padding: 6px;
}}

QMenu::item {{
    padding: 8px 24px 8px 12px;
    border-radius: 8px;
    background: transparent;
}}

QMenu::item:selected {{
    background: {surface_bg};
    color: {title};
}}

QMenu::item:disabled {{
    color: {text_subtle};
}}

QMenu::separator {{
    height: 1px;
    background: {divider};
    margin: 4px 8px;
}}

QFileDialog QFrame,
QMessageBox QFrame {{
    background: transparent;
}}

QToolTip {{
    background: {title};
    color: {panel_bg};
    border: none;
    padding: 6px 8px;
    border-radius: 8px;
}}
""".format(**QSS_COLORS)


def build_app_palette() -> QPalette:
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, color("window_bg"))
    palette.setColor(QPalette.ColorRole.WindowText, color("text"))
    palette.setColor(QPalette.ColorRole.Base, color("field_bg"))
    palette.setColor(QPalette.ColorRole.AlternateBase, color("surface_bg"))
    palette.setColor(QPalette.ColorRole.ToolTipBase, color("title"))
    palette.setColor(QPalette.ColorRole.ToolTipText, color("panel_bg"))
    palette.setColor(QPalette.ColorRole.Text, color("text"))
    palette.setColor(QPalette.ColorRole.Button, color("surface_bg"))
    palette.setColor(QPalette.ColorRole.ButtonText, color("text"))
    palette.setColor(QPalette.ColorRole.BrightText, color("title"))
    palette.setColor(QPalette.ColorRole.Highlight, color("selection"))
    palette.setColor(QPalette.ColorRole.HighlightedText, color("title"))
    palette.setColor(QPalette.ColorRole.Light, color("surface_alt"))
    palette.setColor(QPalette.ColorRole.Midlight, color("surface_bg"))
    palette.setColor(QPalette.ColorRole.Mid, color("border"))
    palette.setColor(QPalette.ColorRole.Dark, color("divider"))
    palette.setColor(QPalette.ColorRole.Shadow, color("window_bg"))
    palette.setColor(QPalette.ColorRole.Link, color("focus"))
    palette.setColor(QPalette.ColorRole.LinkVisited, color("accent_hover"))
    palette.setColor(QPalette.ColorRole.PlaceholderText, color("placeholder"))

    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, color("text_subtle"))
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, color("text_subtle"))
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, color("text_subtle"))
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Highlight, color("divider"))
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.HighlightedText, color("text_muted"))
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.PlaceholderText, color("text_subtle"))
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Base, color("panel_bg"))
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Button, color("panel_bg"))
    return palette
