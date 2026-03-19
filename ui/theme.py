from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPalette

from core.enums import BetType, Flag

# ── Conferix Slate — dark slate base, amber accent, light text ──

COLOR_TOKENS = {
    # ── Surfaces — dark slate ──
    "window_bg": "#252830",
    "panel_bg": "#2C303A",
    "surface_bg": "#31353F",
    "surface_alt": "#373B46",
    "field_bg": "#1E2028",
    "field_hover": "#24272F",
    "field_focus": "#1E2028",
    "toolbar_bg": "#2C303A",
    "footer_bg": "#2C303A",
    # ── Borders — slate, visible ──
    "border": "#4A4E5A",
    "divider": "#3D4150",
    # ── Text — light warm ──
    "title": "#E8E4DC",
    "text": "#D0CCC4",
    "text_muted": "#8A8880",
    "text_subtle": "#666870",
    "placeholder": "#555860",
    # ── Interaction — amber accent ──
    "hover": "#3A3E4A",
    "pressed": "#42464F",
    "focus": "#D48A1C",
    "focus_strong": "#D09028",
    "selection": "#5A4010",
    "accent": "#C07818",
    "accent_hover": "#D48A1C",
    "accent_soft": "#3A2C08",
    # ── Semantic ──
    "success_fg": "#50D080",
    "success_bg": "#1A3028",
    "success_detail": "#40C070",
    "warning_fg": "#F0A030",
    "warning_bg": "#2A2010",
    "warning_soft_bg": "#221A08",
    "warning_detail": "#E09028",
    "danger_fg": "#F06870",
    "danger_bg": "#3A1A1C",
    "danger_soft_bg": "#2E1416",
    "danger_detail": "#E05060",
    "info_fg": "#60A0F0",
    "info_bg": "#1A2840",
    # ── Manual entry ──
    "manual_bg": "#1E2028",
    "manual_border": "#4A4E5A",
    "manual_fg": "#D0CCC4",
    "manual_placeholder": "#666870",
    # ── Column identity — Lançamentos (warm amber/brown, #5A4010 family) ──
    "launch_panel_bg": "#232014",
    "launch_panel_border": "#4A3A18",
    "launch_title_color": "#C09040",
    # ── Column identity — Financeiro (cool teal-slate) ──
    "finance_panel_bg": "#1C2626",
    "finance_panel_border": "#2A3E3E",
    "finance_title_color": "#5C9090",
    # ── Copy button (amber-highlighted) ──
    "copy_btn_bg": "#3A2C08",
    "copy_btn_fg": "#C07818",
    "copy_btn_border": "#5A4010",
    "copy_btn_hover_bg": "#4A3810",
    "copy_btn_hover_fg": "#E09028",
    # ── Result panel ──
    "result_card_bg": "#31353F",
    "result_card_border": "#3D4150",
    "result_prize": "#8A8880",
    "result_value": "#E8E4DC",
    "result_group": "#666870",
    # ── Summary ──
    "summary_section_bg": "#31353F",
    "summary_positive_bg": "#1A3028",
    "summary_positive_fg": "#50D080",
    "summary_negative_bg": "#31353F",
    "summary_negative_fg": "#D0CCC4",
    "summary_detail": "#8A8880",
    # ── Pending panel ──
    "pending_panel_bg": "#2C303A",
    "pending_section_bg": "#2A2010",
    "pending_section_fg": "#F0A030",
    "pending_item_bg": "#31353F",
    "pending_item_fg": "#D0CCC4",
    # ── Finance ──
    "finance_header_bg": "#1C2626",
    "finance_contact_bg": "#223232",
    "finance_row_even": "#1E2A2A",
    "finance_row_odd": "#223232",
    "finance_pending_even": "#262634",
    "finance_pending_odd": "#2C2C3A",
    "finance_winner_even": "#1A3028",
    "finance_winner_odd": "#1E3830",
    "finance_received_bg": "#1A2E2E",
    "finance_received_missing_bg": "#1C2626",
    "finance_received_text": "#80D4D0",
    "finance_received_missing_text": "#4A7070",
    # ── Finance editable field affordance ──
    "finance_editable_hint": "#2C4A4A",
    "finance_editable_border": "#3A6060",
    # ── Bet rows ──
    "winner_row": "#1A3028",
    "error_row": "#3A1A1C",
    "page_header_text": "#E8E4DC",
    "page_total_text": "#D0CCC4",
    "bet_text": "#D0CCC4",
    "empty_text": "#555860",
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
    # Normal block — amber tints (#5A4010 family) for warm identity
    False: {
        "page_header": QColor(90, 64, 16, 70),    # amber wash on page headers
        "page_total": QColor(90, 64, 16, 40),
        "row_light": QColor(192, 120, 24, 14),    # faint amber on bet rows
        "row_dark": QColor(192, 120, 24, 7),
        "empty": QColor(255, 255, 255, 4),
    },
    # Winner block — green family
    True: {
        "page_header": QColor(40, 200, 100, 70),
        "page_total": QColor(40, 200, 100, 48),
        "row_light": QColor(40, 200, 100, 28),
        "row_dark": QColor(40, 200, 100, 18),
        "empty": QColor(40, 200, 100, 8),
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


SELECTION_FILL = QColor(212, 138, 28, 55)
WINNER_FILL = QColor(60, 200, 100, 45)
ERROR_FILL = QColor(224, 80, 80, 40)

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
    "selection_rgba": "rgba(212, 138, 28, 70)",
}


APP_QSS = """
/* ═══════════════════════════════════════════════════
   Conferix — Slate Theme
   Dark slate base, amber accent, light text
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

/* ── Column identity — Lançamentos: warm amber family from #5A4010 ── */

QGroupBox#launchPanel {{
    background: {launch_panel_bg};
    border: 1px solid {launch_panel_border};
    border-radius: 10px;
}}

QGroupBox#launchPanel::title {{
    color: {launch_title_color};
}}

/* ── Column identity — Financeiro: cool teal-slate ── */

QGroupBox#financePanel {{
    background: {finance_panel_bg};
    border: 1px solid {finance_panel_border};
    border-radius: 10px;
}}

QGroupBox#financePanel::title {{
    color: {finance_title_color};
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
    background: transparent;
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
    background: rgba(90, 64, 16, 0.35);
    color: {text};
}}

QToolButton[launchFilter="true"]:checked,
QToolButton[launchCompact="true"]:checked {{
    background: rgba(90, 64, 16, 0.50);
    color: {launch_title_color};
}}

/* ── Copy button — amber-highlighted action ── */

QToolButton[copyButton="true"] {{
    background: {copy_btn_bg};
    border: 1px solid {copy_btn_border};
    border-radius: 6px;
    color: {copy_btn_fg};
    font-size: 8.6pt;
    font-weight: 700;
    padding: 3px 10px;
    min-height: 22px;
}}

QToolButton[copyButton="true"]:hover {{
    background: {copy_btn_hover_bg};
    color: {copy_btn_hover_fg};
    border-color: {accent};
}}

QToolButton[copyButton="true"]:pressed {{
    background: {selection};
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
    border: 1px solid {finance_panel_border};
}}

/* ── Finance — Dinheiro column edit affordance ── */

QTableView#financeTable QLineEdit {{
    background: {finance_received_bg};
    border: 1px solid {finance_editable_border};
    border-radius: 6px;
    color: {finance_received_text};
    font-weight: 740;
    padding: 3px 8px;
}}

QTableView#financeTable QLineEdit:focus {{
    border: 1px solid {focus};
    background: {finance_received_bg};
}}

/* ── Finance totals panel — unified compact card ── */

QGroupBox#financeTotalsPanel {{
    background: transparent;
    margin-top: 4px;
}}

/* Unified summary+saldo card */
QWidget[totalsUnifiedCard="true"] {{
    background: {finance_contact_bg};
    border: 1px solid {finance_panel_border};
    border-radius: 10px;
}}

QWidget[totalsCardHeader="true"] {{
    background: transparent;
    border-bottom: 1px solid {finance_panel_border};
    border-radius: 0;
    padding: 6px 12px 6px 12px;
}}

QLabel[totalsCardTitle="true"] {{
    color: {finance_title_color};
    font-weight: 800;
    font-size: 8.6pt;
    letter-spacing: 0.5px;
}}

QWidget[totalsMetricRow="true"] {{
    background: transparent;
    border: none;
    border-radius: 0;
    padding: 5px 12px;
}}

QLabel[totalsMetricLabel="true"] {{
    color: {text_muted};
    font-weight: 620;
    font-size: 8.5pt;
}}

QLabel[totalsMetricValue="true"] {{
    color: {title};
    font-weight: 760;
    font-size: 11.4pt;
}}

QLineEdit[totalsPaidInput="true"] {{
    background: {finance_received_bg};
    border: 1px solid {finance_editable_border};
    border-radius: 6px;
    padding: 3px 8px;
    color: {finance_received_text};
    font-weight: 720;
    min-height: 22px;
}}

QLineEdit[totalsPaidInput="true"]:focus {{
    border: 1px solid {focus};
}}

QFrame#financeTotalsDivider {{
    color: {finance_panel_border};
    background: {finance_panel_border};
    min-height: 1px;
    max-height: 1px;
    margin: 2px 8px;
}}

/* Saldo inline row */
QWidget[totalsBalanceRow="true"] {{
    background: transparent;
    border: none;
    padding: 6px 12px 8px 12px;
}}

QLabel[totalsBalanceLabel="true"] {{
    color: {text_muted};
    font-weight: 680;
    font-size: 8.4pt;
}}

QGroupBox#financeTotalsPanel QLabel[totalsResult="true"] {{
    font-size: 15.0pt;
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

/* ── BlockMoneyDialog — prompt compacto pós-criação de bloco ── */

QWidget#blockMoneyCard {{
    background: {panel_bg};
    border: 1px solid {launch_panel_border};
    border-radius: 12px;
}}

QLabel[blockMoneyHeader="true"] {{
    color: {title};
    font-size: 10.5pt;
    font-weight: 700;
}}

QLabel[blockMoneyHint="true"] {{
    color: {text_subtle};
    font-size: 8.2pt;
    font-weight: 500;
}}

QPushButton[blockMoneyConfirm="true"] {{
    background: {accent_soft};
    border: 1px solid {copy_btn_border};
    border-radius: 7px;
    color: {focus_strong};
    font-weight: 700;
    min-height: 28px;
    padding: 4px 16px;
}}

QPushButton[blockMoneyConfirm="true"]:hover {{
    background: {accent};
    color: {title};
}}

QPushButton[blockMoneySkip="true"] {{
    background: transparent;
    border: none;
    color: {text_muted};
    font-weight: 600;
    min-height: 28px;
    padding: 4px 10px;
}}

QPushButton[blockMoneySkip="true"]:hover {{
    color: {text};
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
