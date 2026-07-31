"""
app/ui/styles.py

MotorTracker
Estilos globales de la interfaz gráfica.

Este módulo contiene:

- Paleta de colores.
- Tema claro.
- Tema oscuro.
- Estilos reutilizables.
- Funciones para aplicar el tema a QApplication.
"""

from __future__ import annotations

from typing import Final, Literal

from PySide6.QtWidgets import QApplication


ThemeName = Literal[
    "Light",
    "Dark",
]


# ============================================================
# APPLICATION INFORMATION
# ============================================================

APP_TITLE: Final[str] = "MotorTracker"

DEFAULT_THEME: Final[ThemeName] = "Light"


# ============================================================
# LIGHT THEME COLORS
# ============================================================

LIGHT_COLORS: Final[dict[str, str]] = {
    "background": "#F4F6F8",
    "surface": "#FFFFFF",
    "surface_alt": "#F8FAFC",
    "sidebar": "#111827",
    "sidebar_hover": "#1F2937",
    "sidebar_active": "#2563EB",
    "primary": "#2563EB",
    "primary_hover": "#1D4ED8",
    "primary_pressed": "#1E40AF",
    "secondary": "#475569",
    "secondary_hover": "#334155",
    "success": "#16A34A",
    "success_hover": "#15803D",
    "warning": "#D97706",
    "danger": "#DC2626",
    "danger_hover": "#B91C1C",
    "info": "#0284C7",
    "text": "#111827",
    "text_secondary": "#64748B",
    "text_muted": "#94A3B8",
    "text_inverse": "#FFFFFF",
    "border": "#DCE3EA",
    "border_strong": "#CBD5E1",
    "input_background": "#FFFFFF",
    "disabled_background": "#E2E8F0",
    "disabled_text": "#94A3B8",
    "selection": "#DBEAFE",
    "selection_text": "#1E3A8A",
    "table_header": "#EEF2F7",
    "table_alternate": "#F8FAFC",
    "progress_background": "#E2E8F0",
    "shadow": "rgba(15, 23, 42, 0.12)",
}


# ============================================================
# DARK THEME COLORS
# ============================================================

DARK_COLORS: Final[dict[str, str]] = {
    "background": "#0F172A",
    "surface": "#111827",
    "surface_alt": "#1E293B",
    "sidebar": "#020617",
    "sidebar_hover": "#172033",
    "sidebar_active": "#2563EB",
    "primary": "#3B82F6",
    "primary_hover": "#60A5FA",
    "primary_pressed": "#2563EB",
    "secondary": "#64748B",
    "secondary_hover": "#94A3B8",
    "success": "#22C55E",
    "success_hover": "#16A34A",
    "warning": "#F59E0B",
    "danger": "#EF4444",
    "danger_hover": "#DC2626",
    "info": "#38BDF8",
    "text": "#F8FAFC",
    "text_secondary": "#CBD5E1",
    "text_muted": "#94A3B8",
    "text_inverse": "#FFFFFF",
    "border": "#334155",
    "border_strong": "#475569",
    "input_background": "#0F172A",
    "disabled_background": "#1E293B",
    "disabled_text": "#64748B",
    "selection": "#1E3A8A",
    "selection_text": "#DBEAFE",
    "table_header": "#1E293B",
    "table_alternate": "#172033",
    "progress_background": "#334155",
    "shadow": "rgba(0, 0, 0, 0.30)",
}


# ============================================================
# FONT SIZES
# ============================================================

FONT_SIZE_SMALL: Final[int] = 11
FONT_SIZE_NORMAL: Final[int] = 12
FONT_SIZE_MEDIUM: Final[int] = 14
FONT_SIZE_LARGE: Final[int] = 18
FONT_SIZE_TITLE: Final[int] = 24


# ============================================================
# DIMENSIONS
# ============================================================

SIDEBAR_WIDTH: Final[int] = 220
TOP_BAR_HEIGHT: Final[int] = 64

BORDER_RADIUS_SMALL: Final[int] = 6
BORDER_RADIUS_NORMAL: Final[int] = 8
BORDER_RADIUS_LARGE: Final[int] = 12


# ============================================================
# PUBLIC FUNCTIONS
# ============================================================

def get_colors(
    theme: ThemeName | str = DEFAULT_THEME,
) -> dict[str, str]:
    """
    Devuelve la paleta asociada al tema solicitado.
    """

    normalized_theme = normalize_theme(theme)

    if normalized_theme == "Dark":
        return DARK_COLORS.copy()

    return LIGHT_COLORS.copy()


def normalize_theme(
    theme: ThemeName | str | None,
) -> ThemeName:
    """
    Normaliza el nombre del tema.
    """

    normalized = str(
        theme or DEFAULT_THEME
    ).strip().lower()

    if normalized == "dark":
        return "Dark"

    return "Light"


def build_stylesheet(
    theme: ThemeName | str = DEFAULT_THEME,
) -> str:
    """
    Construye el stylesheet global de MotorTracker.
    """

    colors = get_colors(theme)

    return f"""
    /* ======================================================
       GLOBAL
       ====================================================== */

    QWidget {{
        font-family: "Segoe UI", Arial, sans-serif;
        font-size: {FONT_SIZE_NORMAL}px;
        color: {colors["text"]};
        background-color: transparent;
    }}

    QMainWindow {{
        background-color: {colors["background"]};
    }}

    QDialog {{
        background-color: {colors["background"]};
    }}

    QToolTip {{
        color: {colors["text_inverse"]};
        background-color: {colors["sidebar"]};
        border: 1px solid {colors["border_strong"]};
        border-radius: 4px;
        padding: 6px;
    }}

    /* ======================================================
       FRAME AND CARDS
       ====================================================== */

    QFrame#contentFrame {{
        background-color: {colors["background"]};
        border: none;
    }}

    QFrame#card {{
        background-color: {colors["surface"]};
        border: 1px solid {colors["border"]};
        border-radius: {BORDER_RADIUS_LARGE}px;
    }}

    QFrame#summaryCard {{
        background-color: {colors["surface"]};
        border: 1px solid {colors["border"]};
        border-radius: {BORDER_RADIUS_LARGE}px;
    }}

    QFrame#statusCard {{
        background-color: {colors["surface_alt"]};
        border: 1px solid {colors["border"]};
        border-radius: {BORDER_RADIUS_NORMAL}px;
    }}

    QFrame#separator {{
        background-color: {colors["border"]};
        border: none;
        min-height: 1px;
        max-height: 1px;
    }}

    /* ======================================================
       SIDEBAR
       ====================================================== */

    QFrame#sidebar {{
        background-color: {colors["sidebar"]};
        border: none;
    }}

    QLabel#sidebarTitle {{
        color: {colors["text_inverse"]};
        font-size: {FONT_SIZE_LARGE}px;
        font-weight: 700;
        padding: 4px;
    }}

    QLabel#sidebarSubtitle {{
        color: #94A3B8;
        font-size: {FONT_SIZE_SMALL}px;
        padding: 0 4px;
    }}

    QPushButton#sidebarButton {{
        color: #CBD5E1;
        background-color: transparent;
        border: none;
        border-radius: {BORDER_RADIUS_NORMAL}px;
        text-align: left;
        padding: 12px 16px;
        font-size: {FONT_SIZE_NORMAL}px;
        font-weight: 500;
    }}

    QPushButton#sidebarButton:hover {{
        color: {colors["text_inverse"]};
        background-color: {colors["sidebar_hover"]};
    }}

    QPushButton#sidebarButton:checked {{
        color: {colors["text_inverse"]};
        background-color: {colors["sidebar_active"]};
        font-weight: 600;
    }}

    QPushButton#sidebarButton:pressed {{
        background-color: {colors["primary_pressed"]};
    }}

    QLabel#sidebarVersion {{
        color: #64748B;
        font-size: {FONT_SIZE_SMALL}px;
        padding: 6px;
    }}

    /* ======================================================
       TOP BAR
       ====================================================== */

    QFrame#topBar {{
        background-color: {colors["surface"]};
        border: none;
        border-bottom: 1px solid {colors["border"]};
    }}

    QLabel#pageTitle {{
        color: {colors["text"]};
        font-size: {FONT_SIZE_TITLE}px;
        font-weight: 700;
    }}

    QLabel#pageSubtitle {{
        color: {colors["text_secondary"]};
        font-size: {FONT_SIZE_NORMAL}px;
    }}

    QLabel#statusLabel {{
        color: {colors["text_secondary"]};
        background-color: {colors["surface_alt"]};
        border: 1px solid {colors["border"]};
        border-radius: 10px;
        padding: 4px 10px;
    }}

    /* ======================================================
       LABELS
       ====================================================== */

    QLabel#sectionTitle {{
        color: {colors["text"]};
        font-size: {FONT_SIZE_LARGE}px;
        font-weight: 700;
    }}

    QLabel#sectionSubtitle {{
        color: {colors["text_secondary"]};
        font-size: {FONT_SIZE_NORMAL}px;
    }}

    QLabel#cardTitle {{
        color: {colors["text_secondary"]};
        font-size: {FONT_SIZE_SMALL}px;
        font-weight: 600;
    }}

    QLabel#cardValue {{
        color: {colors["text"]};
        font-size: 26px;
        font-weight: 700;
    }}

    QLabel#mutedLabel {{
        color: {colors["text_muted"]};
        font-size: {FONT_SIZE_SMALL}px;
    }}

    QLabel#successLabel {{
        color: {colors["success"]};
        font-weight: 600;
    }}

    QLabel#warningLabel {{
        color: {colors["warning"]};
        font-weight: 600;
    }}

    QLabel#errorLabel {{
        color: {colors["danger"]};
        font-weight: 600;
    }}

    /* ======================================================
       BUTTONS
       ====================================================== */

    QPushButton {{
        min-height: 36px;
        border-radius: {BORDER_RADIUS_NORMAL}px;
        padding: 0 16px;
        font-weight: 600;
    }}

    QPushButton#primaryButton {{
        color: {colors["text_inverse"]};
        background-color: {colors["primary"]};
        border: 1px solid {colors["primary"]};
    }}

    QPushButton#primaryButton:hover {{
        background-color: {colors["primary_hover"]};
        border-color: {colors["primary_hover"]};
    }}

    QPushButton#primaryButton:pressed {{
        background-color: {colors["primary_pressed"]};
        border-color: {colors["primary_pressed"]};
    }}

    QPushButton#secondaryButton {{
        color: {colors["text"]};
        background-color: {colors["surface"]};
        border: 1px solid {colors["border_strong"]};
    }}

    QPushButton#secondaryButton:hover {{
        background-color: {colors["surface_alt"]};
        border-color: {colors["secondary"]};
    }}

    QPushButton#successButton {{
        color: {colors["text_inverse"]};
        background-color: {colors["success"]};
        border: 1px solid {colors["success"]};
    }}

    QPushButton#successButton:hover {{
        background-color: {colors["success_hover"]};
    }}

    QPushButton#dangerButton {{
        color: {colors["text_inverse"]};
        background-color: {colors["danger"]};
        border: 1px solid {colors["danger"]};
    }}

    QPushButton#dangerButton:hover {{
        background-color: {colors["danger_hover"]};
    }}

    QPushButton#textButton {{
        color: {colors["primary"]};
        background-color: transparent;
        border: none;
        padding: 4px 8px;
    }}

    QPushButton#textButton:hover {{
        color: {colors["primary_hover"]};
        text-decoration: underline;
    }}

    QPushButton:disabled {{
        color: {colors["disabled_text"]};
        background-color: {colors["disabled_background"]};
        border-color: {colors["disabled_background"]};
    }}

    /* ======================================================
       INPUTS
       ====================================================== */

    QLineEdit,
    QComboBox,
    QSpinBox,
    QDoubleSpinBox,
    QDateEdit,
    QDateTimeEdit {{
        color: {colors["text"]};
        background-color: {colors["input_background"]};
        border: 1px solid {colors["border_strong"]};
        border-radius: {BORDER_RADIUS_SMALL}px;
        min-height: 36px;
        padding: 0 10px;
        selection-background-color: {colors["selection"]};
        selection-color: {colors["selection_text"]};
    }}

    QLineEdit:focus,
    QComboBox:focus,
    QSpinBox:focus,
    QDoubleSpinBox:focus,
    QDateEdit:focus,
    QDateTimeEdit:focus {{
        border: 1px solid {colors["primary"]};
    }}

    QLineEdit:disabled,
    QComboBox:disabled,
    QSpinBox:disabled,
    QDoubleSpinBox:disabled,
    QDateEdit:disabled,
    QDateTimeEdit:disabled {{
        color: {colors["disabled_text"]};
        background-color: {colors["disabled_background"]};
    }}

    QComboBox::drop-down {{
        width: 28px;
        border: none;
    }}

    QComboBox QAbstractItemView {{
        color: {colors["text"]};
        background-color: {colors["surface"]};
        border: 1px solid {colors["border_strong"]};
        selection-background-color: {colors["selection"]};
        selection-color: {colors["selection_text"]};
        outline: none;
    }}

    QTextEdit,
    QPlainTextEdit {{
        color: {colors["text"]};
        background-color: {colors["input_background"]};
        border: 1px solid {colors["border_strong"]};
        border-radius: {BORDER_RADIUS_SMALL}px;
        padding: 8px;
        selection-background-color: {colors["selection"]};
        selection-color: {colors["selection_text"]};
    }}

    QTextEdit:focus,
    QPlainTextEdit:focus {{
        border: 1px solid {colors["primary"]};
    }}

    /* ======================================================
       CHECKBOX AND RADIO BUTTON
       ====================================================== */

    QCheckBox,
    QRadioButton {{
        spacing: 8px;
        color: {colors["text"]};
    }}

    QCheckBox:disabled,
    QRadioButton:disabled {{
        color: {colors["disabled_text"]};
    }}

    QCheckBox::indicator,
    QRadioButton::indicator {{
        width: 17px;
        height: 17px;
    }}

    /* ======================================================
       TABLES
       ====================================================== */

    QTableWidget,
    QTableView {{
        color: {colors["text"]};
        background-color: {colors["surface"]};
        alternate-background-color: {colors["table_alternate"]};
        border: 1px solid {colors["border"]};
        border-radius: {BORDER_RADIUS_NORMAL}px;
        gridline-color: {colors["border"]};
        selection-background-color: {colors["selection"]};
        selection-color: {colors["selection_text"]};
        outline: none;
    }}

    QHeaderView::section {{
        color: {colors["text"]};
        background-color: {colors["table_header"]};
        border: none;
        border-right: 1px solid {colors["border"]};
        border-bottom: 1px solid {colors["border"]};
        padding: 9px 8px;
        font-weight: 600;
    }}

    QTableCornerButton::section {{
        background-color: {colors["table_header"]};
        border: none;
        border-right: 1px solid {colors["border"]};
        border-bottom: 1px solid {colors["border"]};
    }}

    /* ======================================================
       LISTS AND TREES
       ====================================================== */

    QListWidget,
    QTreeWidget,
    QListView,
    QTreeView {{
        color: {colors["text"]};
        background-color: {colors["surface"]};
        border: 1px solid {colors["border"]};
        border-radius: {BORDER_RADIUS_NORMAL}px;
        outline: none;
        selection-background-color: {colors["selection"]};
        selection-color: {colors["selection_text"]};
    }}

    QListWidget::item,
    QTreeWidget::item {{
        padding: 8px;
    }}

    QListWidget::item:hover,
    QTreeWidget::item:hover {{
        background-color: {colors["surface_alt"]};
    }}

    QListWidget::item:selected,
    QTreeWidget::item:selected {{
        background-color: {colors["selection"]};
        color: {colors["selection_text"]};
    }}

    /* ======================================================
       PROGRESS BAR
       ====================================================== */

    QProgressBar {{
        color: {colors["text"]};
        background-color: {colors["progress_background"]};
        border: none;
        border-radius: 7px;
        min-height: 14px;
        max-height: 14px;
        text-align: center;
        font-size: 10px;
        font-weight: 600;
    }}

    QProgressBar::chunk {{
        background-color: {colors["primary"]};
        border-radius: 7px;
    }}

    QProgressBar#successProgress::chunk {{
        background-color: {colors["success"]};
    }}

    QProgressBar#errorProgress::chunk {{
        background-color: {colors["danger"]};
    }}

    /* ======================================================
       TABS
       ====================================================== */

    QTabWidget::pane {{
        border: 1px solid {colors["border"]};
        border-radius: {BORDER_RADIUS_NORMAL}px;
        background-color: {colors["surface"]};
        top: -1px;
    }}

    QTabBar::tab {{
        color: {colors["text_secondary"]};
        background-color: transparent;
        border: none;
        padding: 10px 16px;
        font-weight: 600;
    }}

    QTabBar::tab:hover {{
        color: {colors["primary"]};
    }}

    QTabBar::tab:selected {{
        color: {colors["primary"]};
        border-bottom: 2px solid {colors["primary"]};
    }}

    /* ======================================================
       SCROLL BARS
       ====================================================== */

    QScrollBar:vertical {{
        background-color: transparent;
        width: 12px;
        margin: 2px;
    }}

    QScrollBar::handle:vertical {{
        background-color: {colors["border_strong"]};
        border-radius: 5px;
        min-height: 30px;
    }}

    QScrollBar::handle:vertical:hover {{
        background-color: {colors["secondary"]};
    }}

    QScrollBar::add-line:vertical,
    QScrollBar::sub-line:vertical {{
        height: 0;
    }}

    QScrollBar::add-page:vertical,
    QScrollBar::sub-page:vertical {{
        background: none;
    }}

    QScrollBar:horizontal {{
        background-color: transparent;
        height: 12px;
        margin: 2px;
    }}

    QScrollBar::handle:horizontal {{
        background-color: {colors["border_strong"]};
        border-radius: 5px;
        min-width: 30px;
    }}

    QScrollBar::handle:horizontal:hover {{
        background-color: {colors["secondary"]};
    }}

    QScrollBar::add-line:horizontal,
    QScrollBar::sub-line:horizontal {{
        width: 0;
    }}

    QScrollBar::add-page:horizontal,
    QScrollBar::sub-page:horizontal {{
        background: none;
    }}

    /* ======================================================
       MENUS
       ====================================================== */

    QMenuBar {{
        color: {colors["text"]};
        background-color: {colors["surface"]};
        border-bottom: 1px solid {colors["border"]};
    }}

    QMenuBar::item {{
        background-color: transparent;
        padding: 7px 10px;
    }}

    QMenuBar::item:selected {{
        background-color: {colors["surface_alt"]};
    }}

    QMenu {{
        color: {colors["text"]};
        background-color: {colors["surface"]};
        border: 1px solid {colors["border"]};
        padding: 5px;
    }}

    QMenu::item {{
        padding: 7px 24px 7px 10px;
        border-radius: 4px;
    }}

    QMenu::item:selected {{
        color: {colors["selection_text"]};
        background-color: {colors["selection"]};
    }}

    QMenu::separator {{
        height: 1px;
        background-color: {colors["border"]};
        margin: 5px 8px;
    }}

    /* ======================================================
       MESSAGE BOX
       ====================================================== */

    QMessageBox {{
        background-color: {colors["surface"]};
    }}

    QMessageBox QLabel {{
        color: {colors["text"]};
        min-width: 280px;
    }}

    /* ======================================================
       GROUP BOX
       ====================================================== */

    QGroupBox {{
        color: {colors["text"]};
        background-color: {colors["surface"]};
        border: 1px solid {colors["border"]};
        border-radius: {BORDER_RADIUS_NORMAL}px;
        margin-top: 12px;
        padding-top: 10px;
        font-weight: 600;
    }}

    QGroupBox::title {{
        subcontrol-origin: margin;
        subcontrol-position: top left;
        left: 12px;
        padding: 0 6px;
        background-color: {colors["surface"]};
    }}

    /* ======================================================
       SPLITTER
       ====================================================== */

    QSplitter::handle {{
        background-color: {colors["border"]};
    }}

    QSplitter::handle:horizontal {{
        width: 1px;
    }}

    QSplitter::handle:vertical {{
        height: 1px;
    }}

    /* ======================================================
       STATUS BAR
       ====================================================== */

    QStatusBar {{
        color: {colors["text_secondary"]};
        background-color: {colors["surface"]};
        border-top: 1px solid {colors["border"]};
    }}

    QStatusBar::item {{
        border: none;
    }}
    """


def apply_theme(
    application: QApplication,
    theme: ThemeName | str = DEFAULT_THEME,
) -> ThemeName:
    """
    Aplica el tema global a la aplicación.

    Returns:
        Nombre normalizado del tema aplicado.
    """

    normalized_theme = normalize_theme(theme)

    application.setStyleSheet(
        build_stylesheet(normalized_theme)
    )

    return normalized_theme


def apply_light_theme(
    application: QApplication,
) -> None:
    """
    Aplica el tema claro.
    """

    apply_theme(
        application,
        "Light",
    )


def apply_dark_theme(
    application: QApplication,
) -> None:
    """
    Aplica el tema oscuro.
    """

    apply_theme(
        application,
        "Dark",
    )


def get_status_color(
    status: str,
    theme: ThemeName | str = DEFAULT_THEME,
) -> str:
    """
    Devuelve un color apropiado para un estado.
    """

    colors = get_colors(theme)

    normalized_status = str(status).strip().lower()

    if normalized_status in {
        "success",
        "completed",
        "complete",
        "ok",
        "imported",
        "valid",
    }:
        return colors["success"]

    if normalized_status in {
        "warning",
        "pending",
        "duplicate",
        "duplicated",
    }:
        return colors["warning"]

    if normalized_status in {
        "error",
        "failed",
        "invalid",
        "cancelled",
        "canceled",
    }:
        return colors["danger"]

    if normalized_status in {
        "running",
        "processing",
        "reading",
        "analyzing",
    }:
        return colors["info"]

    return colors["text_secondary"]