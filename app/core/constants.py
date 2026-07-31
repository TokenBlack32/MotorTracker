"""
app/core/constants.py

MotorTracker
Global Constants
"""

from pathlib import Path

# ==========================================================
# APPLICATION
# ==========================================================

APP_NAME = "MotorTracker"

APP_VERSION = "1.0.0"

APP_AUTHOR = "TokenBlack"

APP_DESCRIPTION = (
    "Motor Report Import System"
)

# ==========================================================
# PATHS
# ==========================================================

ROOT_DIR = Path.cwd()

APP_DIR = ROOT_DIR / "app"

DATABASE_DIR = ROOT_DIR / "Database"

REPORTS_DIR = ROOT_DIR / "Reports"

PROCESSED_DIR = ROOT_DIR / "Processed"

LOGS_DIR = ROOT_DIR / "Logs"

BACKUPS_DIR = ROOT_DIR / "Backups"

ASSETS_DIR = ROOT_DIR / "assets"

ICONS_DIR = ASSETS_DIR / "icons"

IMAGES_DIR = ASSETS_DIR / "images"

TESTS_DIR = ROOT_DIR / "tests"

# ==========================================================
# FILES
# ==========================================================

CONFIG_FILE = ROOT_DIR / "config.json"

DATABASE_FILE = DATABASE_DIR / "MASTER TRACK MOTORES.xlsx"

LOG_FILE = LOGS_DIR / "motortracker.log"

# ==========================================================
# EXCEL
# ==========================================================

SUPPORTED_EXCEL_EXTENSIONS = (
    ".xlsx",
    ".xlsm",
    ".xls"
)

DEFAULT_SHEET_INDEX = 0

HEADER_ROW = 1

# ==========================================================
# IMPORT
# ==========================================================

DEFAULT_DUPLICATE_KEYS = [
    "NCT",
    "VIN"
]

AUTO_PROCESS = False

BACKUP_ENABLED = True

# ==========================================================
# THEMES
# ==========================================================

LIGHT_THEME = "Light"

DARK_THEME = "Dark"

DEFAULT_THEME = LIGHT_THEME

# ==========================================================
# LOGGING
# ==========================================================

LOG_LEVEL = "INFO"

LOG_FORMAT = (
    "{time:YYYY-MM-DD HH:mm:ss} | "
    "{level:<8} | "
    "{message}"
)

# ==========================================================
# STATUS
# ==========================================================

STATUS_NEW = "NEW"

STATUS_DUPLICATE = "DUPLICATE"

STATUS_IMPORTED = "IMPORTED"

STATUS_ERROR = "ERROR"

STATUS_SKIPPED = "SKIPPED"

# ==========================================================
# COLORS
# ==========================================================

SUCCESS_COLOR = "#2ecc71"

WARNING_COLOR = "#f1c40f"

ERROR_COLOR = "#e74c3c"

PRIMARY_COLOR = "#3498db"

# ==========================================================
# UI
# ==========================================================

WINDOW_WIDTH = 1200

WINDOW_HEIGHT = 700

MIN_WIDTH = 900

MIN_HEIGHT = 600

# ==========================================================
# TABLES
# ==========================================================

PREVIEW_ROWS = 100

MAX_LOG_ROWS = 1000

# ==========================================================
# DATE FORMAT
# ==========================================================

DATE_FORMAT = "%d/%m/%Y"

DATETIME_FORMAT = "%d/%m/%Y %H:%M:%S"

TIMESTAMP_FORMAT = "%Y%m%d_%H%M%S"

# ==========================================================
# REPORT MAPPING
# ==========================================================

DEFAULT_MAPPING = {
    "N/C #": "NCT",
    "Part Number": "PN",
    "Supplier": "Supplier",
    "Problem Description": "ISSUE",
    "Comments": "Comments",
    "Department": "Location"
}