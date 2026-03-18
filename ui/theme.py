from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPalette

from core.enums import BetType, Flag

COLOR_TOKENS = {
    # ── Surfaces ──
    "window_bg": "#0B1117",
    "panel_bg": "#101821",
    "surface_bg": "#131C25",
    "surface_alt": "#1A2734",
    "field_bg": "#13202A",
    "field_hover": "#16232C",
    "field_focus": "#182734",
    "toolbar_bg": "#0E161D",
    "footer_bg": "#0D141B",
    # ── Borders ──
    "border": "#1A2631",
    "divider": "#22303C",
    # ── Text ──
    "title": "#F4F8FC",
    "text": "#E3EBF4",
    "text_muted": "#A0B0BF",
    "text_subtle": "#7B8FA0",
    "placeholder": "#748698",
    # ── Interaction ──
    "hover": "#1A2833",
    "pressed": "#21313D",
    "focus": "#4B96AE",
    "focus_strong": "#73C4D5",
    "selection": "#173644",
    "accent": "#2B6E84",
    "accent_hover": "#3E8FA8",
    "accent_soft": "#1A3945",
    # ── Semantic ──
    "success_fg": "#EFFAF4",
    "success_bg": "#234936",
    "success_detail": "#62B189",
    "warning_fg": "#FFF7E8",
    "warning_bg": "#7A6130",
    "warning_soft_bg": "#382C18",
    "warning_detail": "#E1B660",
    "danger_fg": "#FFF1F4",
    "danger_bg": "#6E3542",
    "danger_soft_bg": "#3A1F28",
    "danger_detail": "#D17A88",
    "info_fg": "#EAF4FF",
    "info_bg": "#315B7A",
    # ── Manual entry ──
    "manual_bg": "#24384A",
    "manual_border": "#3F6B8B",
    "manual_fg": "#F0F7FD",
    "manual_placeholder": "#8FA8BE",
    # ── Result panel ──
    "result_card_bg": "#121A22",
    "result_card_border": "#1F2A35",
    "result_prize": "#B9C8D6",
    "result_value": "#F7FBFF",
    "result_group": "#7F93A7",
    # ── Summary ──
    "summary_section_bg": "#18242E",
    "summary_positive_bg": "#18271F",
    "summary_positive_fg": "#EAFBF1",
    "summary_negative_bg": "#1C2731",
    "summary_negative_fg": "#E5EEF7",
    "summary_detail": "#AAB8C5",
    # ── Pending panel ──
    "pending_panel_bg": "#101820",
    "pending_section_bg": "#25251D",
    "pending_section_fg": "#FFF4DD",
    "pending_item_bg": "#131B23",
    "pending_item_fg": "#D8E4EF",
    # ── Finance ──
    "finance_header_bg": "#0E161C",
    "finance_contact_bg": "#16212A",
    "finance_row_even": "#10161B",
    "finance_row_odd": "#10171C",
    "finance_pending_even": "#11171C",
    "finance_pending_odd": "#11181D",
    "finance_winner_even": "#111916",
    "finance_winner_odd": "#111A17",
    "finance_received_bg": "#121B22",
    "finance_received_missing_bg": "#10171C",
    "finance_received_text": "#EEF6FC",
    "finance_received_missing_text": "#8A9CAB",
    # ── Bet rows ──
    "winner_row": "#15231C",
    "error_row": "#341F26",
    "page_header_text": "#F3F7FB",
    "page_total_text": "#E8EEF5",
    "bet_text": "#E8EEF5",
    "empty_text": "#7F8C99",
    # ── Type badges ──
    "badge_centena_fg": "#EAF4FF",
    "badge_centena_bg": "#315B7A",
    "badge_milhar_fg": "#EAFBF2",
    "badge_milhar_bg": "#2E6B4A",
    "badge_mc_fg": "#F4EDFF",
    "badge_mc_bg": "#594A80",
    "badge_dezena_fg": "#FFF8E7",
    "badge_dezena_bg": "#8C6A2B",
    "badge_duque_fg": "#FFF1E8",
    "badge_duque_bg": "#9A5A2C",
    "badge_terno_fg": "#FFF0EC",
    "badge_terno_bg": "#7A3F35",
    "badge_grupo_fg": "#F4FADF",
    "badge_grupo_bg": "#556B2F",
    "badge_terno_grupo_fg": "#E9FFFC",
    "badge_terno_grupo_bg": "#2D7A74",
    "badge_fechamento_fg": "#EDF5FF",
    "badge_fechamento_bg": "#4A617A",
    # ── Flag badges ──
    "flag_invertida_fg": "#F1ECFF",
    "flag_invertida_bg": "#4A4B83",
    "flag_de_fg": "#FFF7E8",
    "flag_de_bg": "#8A6830",
    "flag_dem_fg": "#FFF0F4",
    "flag_dem_bg": "#77485A",
}

BLOCK_PALETTES = {
    False: {
        "page_header": QColor(22, 33, 42, 102),
        "page_total": QColor(18, 26, 34, 84),
        "row_light": QColor(18, 27, 35, 54),
        "row_dark": QColor(16, 24, 31, 32),
        "empty": QColor(18, 27, 35, 18),
    },
    True: {
        "page_header": QColor(24, 36, 46, 102),
        "page_total": QColor(20, 29, 37, 84),
        "row_light": QColor(20, 30, 38, 54),
        "row_dark": QColor(17, 26, 34, 32),
        "empty": QColor(18, 27, 35, 18),
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


SELECTION_FILL = QColor(45, 77, 87, 122)
WINNER_FILL = QColor(28, 67, 45, 46)
ERROR_FILL = QColor(74, 38, 48, 50)

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
    "selection_rgba": "rgba(45, 77, 87, 210)",
}


APP_QSS = """
/* ═══════════════════════════════════════════════════
   Conferix Theme — Consolidated
   ═══════════════════════════════════════════════════ */

/* ── Global ── */

QMainWindow {{
    background: {window_bg};
}}

QWidget {{
    color: {text};
    background: transparent;
    font-family: "Segoe UI Variable Text", "Segoe UI";
    font-size: 11.0pt;
    selection-background-color: {selection};
    selection-color: {title};
}}

QWidget#middlePanel,
QScrollArea > QWidget > QWidget {{
    background: transparent;
}}

/* ── Toolbar ── */

QToolBar#mainToolbar {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #0E151A, stop:1 #0B1116);
    border: 1px solid #16232D;
    border-radius: 24px;
    spacing: 8px;
    padding: 10px 18px;
    margin: 8px 12px 0 12px;
}}

QToolBar#mainToolbar::separator {{
    width: 1px;
    margin: 8px 4px;
    background: {border};
}}

QToolBar#mainToolbar QToolButton {{
    min-height: 34px;
    padding: 6px 14px;
    border-radius: 13px;
    font-size: 9.6pt;
    font-weight: 650;
}}

QToolBar#mainToolbar QToolButton[toolbarTone="menu"] {{
    background: #111A21;
    border: 1px solid #1F2E39;
    color: #DDE8F0;
    padding-right: 18px;
}}

QToolBar#mainToolbar QToolButton[toolbarTone="menu"]:hover {{
    background: {hover};
    border-color: {accent_hover};
}}

QToolBar#mainToolbar QToolButton[toolbarTone="quiet"] {{
    background: transparent;
    border: 1px solid transparent;
    color: #95A7B6;
}}

QToolBar#mainToolbar QToolButton[toolbarTone="quiet"]:hover {{
    background: #121C24;
    border: 1px solid #1D2D39;
    color: #E3ECF4;
}}

QToolBar#mainToolbar QToolButton[toolbarTone="primary"] {{
    background: {accent_soft};
    border: 1px solid #2F6175;
    color: #F3F8FC;
}}

QToolBar#mainToolbar QToolButton[toolbarTone="primary"]:hover {{
    background: #285160;
    border-color: {focus};
}}

QToolBar#mainToolbar QToolButton[toolbarTone="accent"] {{
    background: #2A5B6F;
    border: 1px solid #4C8EAA;
    color: #F5FBFF;
    font-weight: 700;
}}

QToolBar#mainToolbar QToolButton[toolbarTone="accent"]:hover {{
    background: #336777;
    border-color: {focus};
}}

QToolBar#mainToolbar QToolButton::menu-indicator {{
    subcontrol-origin: padding;
    subcontrol-position: right center;
    right: 8px;
}}

/* ── Labels ── */

QLabel[topTitle="true"] {{
    font-size: 16.1pt;
    font-weight: 760;
    color: {title};
}}

QLabel[toolbarLabel="true"] {{
    color: #8196A8;
    font-size: 8.5pt;
    font-weight: 650;
    padding-right: 4px;
}}

QLabel[toolbarMeta="true"] {{
    color: #7F92A2;
    font-size: 8.5pt;
    font-weight: 600;
}}

/* ── Generic buttons ── */

QToolButton,
QPushButton {{
    background: #1E2730;
    color: #EEF4FA;
    border: 1px solid #30414F;
    border-radius: 9px;
    min-height: 26px;
    padding: 4px 12px;
    font-weight: 600;
}}

QToolButton:hover,
QPushButton:hover {{
    background: {hover};
    border-color: {accent_hover};
}}

QToolButton:pressed,
QPushButton:pressed {{
    background: {pressed};
    border-color: {focus};
}}

QToolButton:disabled,
QPushButton:disabled {{
    background: {panel_bg};
    color: {text_subtle};
    border-color: {divider};
}}

QDialogButtonBox QPushButton {{
    min-height: 28px;
    min-width: 92px;
}}

/* ── GroupBox / Panels ── */

QGroupBox {{
    font-size: 11.5pt;
    font-weight: 700;
    color: {title};
    background: #0F161C;
    border: 1px solid #16222B;
    border-radius: 20px;
    margin-top: 14px;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    left: 16px;
    padding: 0 4px;
    font-size: 12.0pt;
    font-weight: 700;
    color: {title};
}}

QGroupBox#launchPanel,
QGroupBox#financePanel {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #111922, stop:1 #0D1319);
}}

QGroupBox#resultPanel,
QGroupBox#sessionOverviewPanel,
QGroupBox#pendingPanel,
QGroupBox#financeTotalsPanel {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #121B23, stop:1 #0F151C);
}}

/* ── Tables ── */

QTableView {{
    background: {surface_bg};
    alternate-background-color: {surface_bg};
    border: 1px solid {border};
    border-radius: 14px;
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
    border: 1px solid {border};
    border-radius: 9px;
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
    border-color: {divider};
}}

QComboBox {{
    min-height: 26px;
    padding-right: 28px;
}}

QComboBox::drop-down {{
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 24px;
    border-left: 1px solid {divider};
    background: {surface_alt};
    border-top-right-radius: 9px;
    border-bottom-right-radius: 9px;
}}

QComboBox QAbstractItemView,
QMenu,
QFileDialog QListView,
QFileDialog QTreeView {{
    background: {surface_bg};
    color: {text};
    border: 1px solid {border};
    selection-background-color: {selection};
    selection-color: {title};
    outline: 0;
}}

QAbstractSpinBox::up-button,
QAbstractSpinBox::down-button {{
    width: 18px;
    background: {surface_alt};
    border-left: 1px solid {divider};
}}

QAbstractSpinBox::up-button:hover,
QAbstractSpinBox::down-button:hover {{
    background: {hover};
}}

/* ── Search widget ── */

QWidget#toolbarSearchWidget {{
    background: #0E151B;
    border: 1px solid #1A2832;
    border-radius: 20px;
    padding: 4px 8px 4px 12px;
}}

QComboBox#toolbarBlockSearch {{
    min-height: 40px;
    min-width: 204px;
    padding: 6px 44px 6px 14px;
    background: #0C1318;
    border: 1px solid #294255;
    border-radius: 15px;
    color: {title};
    font-size: 10.1pt;
    font-weight: 700;
}}

QComboBox#toolbarBlockSearch:hover {{
    background: #111B22;
    border-color: #3D6178;
}}

QComboBox#toolbarBlockSearch:focus {{
    background: #12202A;
    border: 1px solid {focus};
}}

QComboBox#toolbarBlockSearch::drop-down {{
    width: 36px;
    border-left: 1px solid #355569;
    background: #14232D;
    border-top-right-radius: 15px;
    border-bottom-right-radius: 15px;
}}

QComboBox#toolbarBlockSearch QLineEdit {{
    background: transparent;
    border: none;
    padding: 0;
    color: {title};
}}

QComboBox#toolbarBlockSearch QAbstractItemView {{
    background: {surface_bg};
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
    border-radius: 12px;
    background: transparent;
    border: 1px solid transparent;
    color: #91A4B5;
    font-size: 10.5pt;
    font-weight: 700;
}}

QToolButton#toolbarSearchClear:hover {{
    background: #182631;
    border-color: #315165;
    color: {title};
}}

/* ── Launch filters ── */

QWidget#launchFiltersBar {{
    background: #0F171D;
    border: 1px solid #18252E;
    border-radius: 16px;
    padding: 4px 6px;
}}

QToolButton[launchFilter="true"],
QToolButton[launchCompact="true"] {{
    min-height: 30px;
    padding: 4px 12px;
    border-radius: 12px;
    background: transparent;
    border: 1px solid transparent;
    color: #8EA1B2;
    font-size: 9.1pt;
    font-weight: 700;
}}

QToolButton[launchFilter="true"]:hover,
QToolButton[launchCompact="true"]:hover {{
    background: #131E27;
    border: 1px solid #213240;
    color: {title};
}}

QToolButton[launchFilter="true"]:checked,
QToolButton[launchCompact="true"]:checked {{
    background: #162631;
    border: 1px solid #2D4D5F;
    color: {title};
}}

/* ── Scrollbars ── */

QAbstractScrollArea,
QScrollArea {{
    border: none;
}}

QScrollBar:vertical {{
    background: {panel_bg};
    width: 12px;
    margin: 4px 2px 4px 2px;
}}

QScrollBar::handle:vertical {{
    background: {border};
    min-height: 24px;
    border-radius: 6px;
}}

QScrollBar::handle:vertical:hover {{
    background: {focus};
}}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical,
QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical {{
    background: none;
    border: none;
}}

QScrollBar:horizontal {{
    background: {panel_bg};
    height: 12px;
    margin: 2px 4px 2px 4px;
}}

QScrollBar::handle:horizontal {{
    background: {border};
    min-width: 24px;
    border-radius: 6px;
}}

QScrollBar::handle:horizontal:hover {{
    background: {focus};
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
    background: {window_bg};
}}

QSplitter::handle:hover {{
    background: {accent};
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

/* ── Result panel ── */

QGroupBox#resultPanel QFrame[resultRow="true"] {{
    background: transparent;
    border: none;
    border-bottom: 1px solid #1A2832;
    border-radius: 0;
}}

QGroupBox#resultPanel QFrame[resultTopPrize="true"] {{
    border-bottom: 1px solid #233848;
}}

QLabel[resultPrize="true"] {{
    color: #8DA0B1;
    font-size: 7.8pt;
    font-weight: 700;
    min-width: 66px;
}}

QLabel[resultValue="true"] {{
    color: #F5FAFE;
    font-size: 16.2pt;
    font-weight: 780;
}}

QLabel[resultGroup="true"] {{
    color: #738798;
    font-size: 7.5pt;
    font-weight: 620;
    min-width: 76px;
}}

/* ── Summary panel ── */

QWidget[summaryRow="true"][summaryKind="section"] {{
    background: {summary_section_bg};
    border: 1px solid {border};
    border-radius: 9px;
}}

/* ── Session overview ── */

QToolButton[overviewTab="true"] {{
    min-height: 30px;
    padding: 5px 12px;
    border-radius: 12px;
    background: transparent;
    border: 1px solid transparent;
    color: #8CA0B1;
    font-size: 9.8pt;
    font-weight: 700;
}}

QToolButton[overviewTab="true"]:checked {{
    background: #15222C;
    border: 1px solid #284253;
    color: {title};
}}

QToolButton[overviewTab="true"]:hover {{
    border-color: {accent_hover};
}}

QToolButton[overviewRow="true"] {{
    text-align: left;
    padding: 12px 10px;
    border-radius: 14px;
    font-size: 9.85pt;
    border: 1px solid transparent;
}}

QToolButton[overviewRow="true"][overviewKind="block"] {{
    background: transparent;
    border-bottom: 1px solid #17252F;
    color: #E8F1F8;
}}

QToolButton[overviewRow="true"][overviewKind="block"]:hover {{
    background: rgba(22, 35, 45, 0.55);
    border: 1px solid rgba(39, 66, 84, 0.72);
}}

QToolButton[overviewRow="true"][overviewKind="block"][overviewSelected="true"] {{
    background: rgba(24, 40, 50, 0.85);
    border: 1px solid #2B4C60;
}}

QWidget[overviewAwardedGroup="true"] {{
    background: transparent;
    border: 1px solid #15242C;
    border-radius: 16px;
    padding: 2px;
}}

QWidget[overviewAwardedGroup="true"][overviewSelected="true"] {{
    border-color: #2C4B5D;
}}

QToolButton[overviewRow="true"][overviewKind="awarded"] {{
    background: rgba(18, 30, 26, 0.42);
    border: 1px solid rgba(54, 89, 74, 0.48);
    color: #EEF8F1;
    font-weight: 700;
}}

QToolButton[overviewRow="true"][overviewKind="awarded"]:hover {{
    background: rgba(23, 37, 32, 0.66);
    border-color: rgba(82, 133, 109, 0.64);
}}

QWidget[overviewDetails="true"] {{
    background: transparent;
}}

QWidget[overviewDetailRow="true"] {{
    background: rgba(17, 25, 31, 0.38);
    border: 1px solid rgba(31, 49, 61, 0.54);
    border-radius: 12px;
}}

QLabel[overviewDetailBet="true"] {{
    color: #F2F7FB;
    font-size: 9.35pt;
    font-weight: 720;
}}

QLabel[overviewDetailMeta="true"] {{
    color: #91A5B5;
    font-size: 8.45pt;
    font-weight: 620;
}}

QLabel[overviewDetailPrize="true"] {{
    color: #7BC297;
    font-size: 8.6pt;
    font-weight: 700;
}}

QLabel[overviewEmpty="true"] {{
    color: {text_subtle};
    font-size: 10.0pt;
    background: #0E151A;
    border: 1px dashed #203140;
    border-radius: 16px;
    padding: 14px;
}}

/* ── Pendency panel ── */

QGroupBox#pendingPanel QLabel[pendencySectionHeader="true"] {{
    font-weight: 700;
    font-size: 8.8pt;
    padding: 2px 2px 0 2px;
}}

QGroupBox#pendingPanel QLabel[pendencySectionHeader="true"][pendencyTone="critical"] {{
    color: {warning_detail};
}}

QGroupBox#pendingPanel QLabel[pendencySectionHeader="true"][pendencyTone="warning"] {{
    color: {text_muted};
}}

QWidget[pendencyGroup="true"] {{
    background: transparent;
    border: 1px solid transparent;
    border-radius: 14px;
}}

QWidget[pendencyGroup="true"][pendencyTone="critical"] {{
    background: rgba(46, 35, 24, 0.24);
    border: 1px solid rgba(138, 108, 58, 0.46);
}}

QWidget[pendencyGroup="true"][pendencyTone="warning"] {{
    background: rgba(26, 32, 37, 0.22);
    border: 1px solid rgba(56, 78, 92, 0.44);
}}

QWidget[pendencyGroup="true"][pendencyExpanded="true"][pendencyTone="critical"] {{
    background: rgba(50, 38, 25, 0.34);
}}

QWidget[pendencyGroup="true"][pendencyExpanded="true"][pendencyTone="warning"] {{
    background: rgba(24, 32, 39, 0.34);
}}

QToolButton[pendencySummaryButton="true"] {{
    text-align: left;
    padding: 7px 10px;
    border: none;
    border-radius: 12px;
    font-size: 9.55pt;
    font-weight: 700;
    background: transparent;
}}

QToolButton[pendencySummaryButton="true"][pendencyExpanded="true"] {{
    background: rgba(255, 255, 255, 0.02);
}}

QToolButton[pendencySummaryButton="true"][pendencyTone="critical"] {{
    color: #F4EDDD;
}}

QToolButton[pendencySummaryButton="true"][pendencyTone="warning"] {{
    color: #DDE8F1;
}}

QToolButton[pendencySummaryButton="true"]:hover {{
    background: rgba(115, 196, 213, 0.045);
}}

QWidget[pendencyDetails="true"] {{
    background: transparent;
    border-top: 1px solid rgba(33, 49, 59, 0.55);
}}

QLabel[pendencyDetail="true"] {{
    color: #D1C6A9;
    line-height: 1.3;
    font-size: 8.7pt;
}}

QLabel[pendencyEmpty="true"] {{
    color: {text_subtle};
    font-size: 10.0pt;
    border: 1px dashed #223543;
    border-radius: 14px;
    background: #111922;
    padding: 14px;
}}

/* ── Finance table ── */

QTableView#financeTable {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #0F171D, stop:1 #0C1217);
    border: 1px solid #16242D;
    border-radius: 18px;
    padding: 4px 0 4px 0;
    selection-background-color: transparent;
}}

QTableView#financeTable::item {{
    padding: 0 10px;
    border: none;
}}

QTableView#financeTable:focus {{
    border: 1px solid #2A5062;
}}

/* ── Finance totals panel ── */

QWidget[totalsMetricsGroup="true"] {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #101820, stop:1 #0E151B);
    border: 1px solid #192833;
    border-radius: 16px;
}}

QWidget[totalsMetricRow="true"] {{
    background: transparent;
    border: none;
    border-radius: 0;
    padding: 7px 12px;
}}

QLabel[totalsMetricLabel="true"] {{
    color: #8DA0B1;
    font-weight: 620;
    font-size: 8.7pt;
}}

QLabel[totalsMetricValue="true"] {{
    color: #F4F9FD;
    font-weight: 760;
    font-size: 12.3pt;
}}

QLineEdit[totalsPaidInput="true"] {{
    background: #0F171C;
    border: 1px solid #1E2D38;
    border-radius: 12px;
    padding: 6px 10px;
    color: #F2F8FD;
    font-weight: 740;
}}

QGroupBox#financeTotalsPanel QLineEdit {{
    background: #0D151B;
    border: 1px solid #21313D;
    border-radius: 12px;
    min-height: 32px;
}}

QGroupBox#financeTotalsPanel QLineEdit:focus {{
    border: 1px solid {focus};
}}

QFrame#financeTotalsDivider {{
    color: #17242D;
    background: #17242D;
    min-height: 1px;
    max-height: 1px;
    margin: 2px 8px 4px 8px;
}}

QWidget[totalsBalanceCard="true"] {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #15212B, stop:1 #101821);
    border: 1px solid #25384A;
    border-radius: 18px;
}}

QLabel[totalsBalanceLabel="true"] {{
    color: #8FA3B4;
    font-weight: 700;
    font-size: 8.4pt;
}}

QGroupBox#financeTotalsPanel QLabel[totalsResult="true"] {{
    font-size: 23.0pt;
    font-weight: 820;
    qproperty-alignment: AlignRight;
}}

QGroupBox#financeTotalsPanel QLabel[totalsResult="true"][cashTone="positive"] {{
    color: #58A97D;
}}

QGroupBox#financeTotalsPanel QLabel[totalsResult="true"][cashTone="negative"] {{
    color: #C66A78;
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
    background: #0F171C;
    border: 1px solid #192833;
    color: #DDE7F0;
    border-radius: 14px;
    padding: 9px 10px;
    placeholder-text-color: #5F7283;
}}

QPlainTextEdit#sessionNotes:focus {{
    border: 1px solid #335D72;
}}

/* ── Bottom bar ── */

QWidget#bottomBar {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0E151B, stop:0.45 #101821, stop:1 #0D141A);
    border: 1px solid #16232C;
    border-radius: 18px;
    padding: 2px 6px;
}}

QWidget[bottomZone="context"] {{
    background: rgba(18, 28, 35, 0.7);
    border: 1px solid rgba(31, 48, 60, 0.88);
    border-radius: 14px;
    padding: 0 10px;
}}

QWidget[bottomZone="metrics"],
QWidget[bottomZone="shortcuts"],
QWidget[bottomSegment="true"],
QWidget[bottomMetricsGroup="true"] {{
    background: transparent;
}}

QLabel[bottomContext="true"] {{
    color: #F2F8FC;
    font-weight: 760;
    font-size: 10.6pt;
}}

QLabel[bottomInlineLabel="true"] {{
    color: #7F93A4;
    font-weight: 620;
    font-size: 8.25pt;
}}

QLabel[bottomInlineValue="true"] {{
    color: #DDE8F0;
    font-weight: 640;
    font-size: 9.45pt;
}}

QLabel[bottomInlineValueStrong="true"] {{
    color: #F5FAFE;
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
    background: #10181E;
    border: 1px solid #1E303B;
    min-height: 30px;
    padding: 3px 30px 3px 12px;
    font-weight: 700;
    border-radius: 12px;
    color: #DDE8F0;
}}

QComboBox#bottomBlockSelector::drop-down {{
    width: 22px;
    border: none;
}}

QComboBox#bottomBlockSelector:hover,
QComboBox#bottomBlockSelector:focus {{
    background: #111B22;
    border-color: #294050;
    color: {title};
}}

QFrame[bottomSeparator="true"] {{
    color: transparent;
    background: transparent;
    min-width: 0;
    max-width: 0;
}}

QLabel[bottomHint="true"] {{
    color: #6F8393;
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
    border-radius: 12px;
    padding: 8px;
}}

QMenu::item {{
    padding: 8px 24px 8px 12px;
    border-radius: 8px;
    background: transparent;
}}

QMenu::item:selected {{
    background: {surface_alt};
    color: {title};
}}

QMenu::item:disabled {{
    color: {text_subtle};
}}

QMenu::separator {{
    height: 1px;
    background: {divider};
    margin: 6px 10px;
}}

QFileDialog QFrame,
QMessageBox QFrame {{
    background: transparent;
}}

QToolTip {{
    background: {surface_alt};
    color: {text};
    border: 1px solid {border};
    padding: 6px 8px;
    border-radius: 10px;
}}
""".format(**QSS_COLORS)


def build_app_palette() -> QPalette:
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, color("window_bg"))
    palette.setColor(QPalette.ColorRole.WindowText, color("text"))
    palette.setColor(QPalette.ColorRole.Base, color("field_bg"))
    palette.setColor(QPalette.ColorRole.AlternateBase, color("surface_bg"))
    palette.setColor(QPalette.ColorRole.ToolTipBase, color("surface_alt"))
    palette.setColor(QPalette.ColorRole.ToolTipText, color("text"))
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
