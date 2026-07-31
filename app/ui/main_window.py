"""
app/ui/main_window.py

MotorTracker
Ventana principal de la aplicación.

La interfaz permite:

- Consultar reportes pendientes.
- Seleccionar un reporte.
- Mostrar una vista previa.
- Analizar registros.
- Importar registros nuevos.
- Mostrar progreso.
- Mostrar resultados.
- Cambiar entre tema claro y oscuro.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QAction, QCloseEvent
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QStackedWidget,
    QStatusBar,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.core.config_manager import ConfigManager
from app.services.import_service import ImportService
from app.ui.styles import (
    APP_TITLE,
    DEFAULT_THEME,
    SIDEBAR_WIDTH,
    apply_theme,
    normalize_theme,
)
from app.ui.workers.import_worker import ImportWorker
from app.utils.logger import LoggerManager


class MainWindow(QMainWindow):
    """
    Ventana principal de MotorTracker.
    """

    theme_changed = Signal(str)

    PREVIEW_COLUMNS = [
        ("model", "Model"),
        ("part_number", "PN"),
        ("supplier", "Supplier"),
        ("traceability", "Traceability"),
        ("vin", "VIN"),
        ("nct", "NCT"),
        ("dtc", "DTC"),
        ("issue", "Issue"),
        ("location", "Location"),
        ("comments", "Comments"),
        ("disposition", "Disposition"),
        ("ica", "ICA"),
        ("rca", "RCA"),
        ("pca", "PCA"),
        ("status", "Status"),
        ("is_valid", "Valid"),
    ]

    def __init__(
        self,
        parent: QWidget | None = None,
    ) -> None:
        """
        Inicializa la ventana principal.
        """

        super().__init__(parent)

        self.config = ConfigManager()
        self.service = ImportService()

        self.current_theme = normalize_theme(
            self.config.get(
                "ui.theme",
                DEFAULT_THEME,
            )
        )

        self.current_report: Path | None = None

        self.worker_thread: QThread | None = None
        self.worker: ImportWorker | None = None

        self.last_analysis: dict[str, Any] | None = None
        self.last_import: dict[str, Any] | None = None

        self._setup_window()
        self._build_ui()
        self._connect_signals()
        self._apply_current_theme()
        self.refresh_data()

    # =========================================================
    # WINDOW SETUP
    # =========================================================

    def _setup_window(self) -> None:
        """
        Configura las propiedades generales de la ventana.
        """

        self.setWindowTitle(APP_TITLE)

        self.resize(
            1400,
            850,
        )

        self.setMinimumSize(
            1100,
            700,
        )

    # =========================================================
    # UI CREATION
    # =========================================================

    def _build_ui(self) -> None:
        """
        Construye todos los componentes de la interfaz.
        """

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )
        main_layout.setSpacing(0)

        self.sidebar = self._create_sidebar()
        self.content = self._create_content()

        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(
            self.content,
            1,
        )

        self._create_status_bar()
        self._create_menu()

    def _create_sidebar(self) -> QFrame:
        """
        Crea la barra lateral.
        """

        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(SIDEBAR_WIDTH)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(
            16,
            24,
            16,
            20,
        )
        layout.setSpacing(8)

        title = QLabel("MotorTracker")
        title.setObjectName("sidebarTitle")

        subtitle = QLabel(
            "Engine report manager"
        )
        subtitle.setObjectName("sidebarSubtitle")

        layout.addWidget(title)
        layout.addWidget(subtitle)

        layout.addSpacing(24)

        self.dashboard_button = self._create_sidebar_button(
            "Dashboard",
            0,
            checked=True,
        )

        self.reports_button = self._create_sidebar_button(
            "Reports",
            1,
        )

        self.preview_button = self._create_sidebar_button(
            "Preview",
            2,
        )

        self.settings_button = self._create_sidebar_button(
            "Settings",
            3,
        )

        layout.addWidget(self.dashboard_button)
        layout.addWidget(self.reports_button)
        layout.addWidget(self.preview_button)
        layout.addWidget(self.settings_button)

        layout.addStretch()

        self.sidebar_status_label = QLabel(
            "Ready"
        )
        self.sidebar_status_label.setObjectName(
            "sidebarSubtitle"
        )

        version = self.config.get(
            "version",
            "1.0.0",
        )

        version_label = QLabel(
            f"Version {version}"
        )
        version_label.setObjectName(
            "sidebarVersion"
        )

        layout.addWidget(
            self.sidebar_status_label
        )
        layout.addWidget(version_label)

        return sidebar

    def _create_sidebar_button(
        self,
        text: str,
        page_index: int,
        checked: bool = False,
    ) -> QPushButton:
        """
        Crea un botón de navegación.
        """

        button = QPushButton(text)
        button.setObjectName("sidebarButton")
        button.setCheckable(True)
        button.setChecked(checked)
        button.setProperty(
            "page_index",
            page_index,
        )

        return button

    def _create_content(self) -> QFrame:
        """
        Crea la zona principal.
        """

        content = QFrame()
        content.setObjectName("contentFrame")

        layout = QVBoxLayout(content)
        layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )
        layout.setSpacing(0)

        self.top_bar = self._create_top_bar()
        self.pages = QStackedWidget()

        self.pages.addWidget(
            self._create_dashboard_page()
        )
        self.pages.addWidget(
            self._create_reports_page()
        )
        self.pages.addWidget(
            self._create_preview_page()
        )
        self.pages.addWidget(
            self._create_settings_page()
        )

        layout.addWidget(self.top_bar)
        layout.addWidget(
            self.pages,
            1,
        )

        return content

    def _create_top_bar(self) -> QFrame:
        """
        Crea la barra superior.
        """

        frame = QFrame()
        frame.setObjectName("topBar")
        frame.setFixedHeight(76)

        layout = QHBoxLayout(frame)
        layout.setContentsMargins(
            28,
            10,
            28,
            10,
        )

        title_layout = QVBoxLayout()
        title_layout.setSpacing(2)

        self.page_title = QLabel(
            "Dashboard"
        )
        self.page_title.setObjectName(
            "pageTitle"
        )

        self.page_subtitle = QLabel(
            "MotorTracker general status"
        )
        self.page_subtitle.setObjectName(
            "pageSubtitle"
        )

        title_layout.addWidget(
            self.page_title
        )
        title_layout.addWidget(
            self.page_subtitle
        )

        self.top_status_label = QLabel(
            "Ready"
        )
        self.top_status_label.setObjectName(
            "statusLabel"
        )

        self.refresh_button = QPushButton(
            "Refresh"
        )
        self.refresh_button.setObjectName(
            "secondaryButton"
        )

        layout.addLayout(title_layout)
        layout.addStretch()
        layout.addWidget(
            self.top_status_label
        )
        layout.addWidget(
            self.refresh_button
        )

        return frame

    # =========================================================
    # DASHBOARD PAGE
    # =========================================================

    def _create_dashboard_page(self) -> QWidget:
        """
        Crea la página Dashboard.
        """

        page = QWidget()

        layout = QVBoxLayout(page)
        layout.setContentsMargins(
            28,
            24,
            28,
            24,
        )
        layout.setSpacing(20)

        summary_layout = QHBoxLayout()
        summary_layout.setSpacing(16)

        self.pending_card = self._create_summary_card(
            "Pending reports",
            "0",
        )

        self.database_card = self._create_summary_card(
            "Database",
            "Not found",
        )

        self.new_card = self._create_summary_card(
            "New records",
            "0",
        )

        self.duplicate_card = self._create_summary_card(
            "Duplicates",
            "0",
        )

        summary_layout.addWidget(
            self.pending_card["frame"]
        )
        summary_layout.addWidget(
            self.database_card["frame"]
        )
        summary_layout.addWidget(
            self.new_card["frame"]
        )
        summary_layout.addWidget(
            self.duplicate_card["frame"]
        )

        layout.addLayout(summary_layout)

        operation_card = QFrame()
        operation_card.setObjectName("card")

        operation_layout = QVBoxLayout(
            operation_card
        )
        operation_layout.setContentsMargins(
            22,
            20,
            22,
            20,
        )
        operation_layout.setSpacing(14)

        operation_title = QLabel(
            "Current operation"
        )
        operation_title.setObjectName(
            "sectionTitle"
        )

        self.selected_report_label = QLabel(
            "No report selected"
        )
        self.selected_report_label.setObjectName(
            "sectionSubtitle"
        )

        buttons_layout = QHBoxLayout()

        self.analyze_latest_button = QPushButton(
            "Analyze latest report"
        )
        self.analyze_latest_button.setObjectName(
            "secondaryButton"
        )

        self.import_latest_button = QPushButton(
            "Import latest report"
        )
        self.import_latest_button.setObjectName(
            "primaryButton"
        )

        self.cancel_button = QPushButton(
            "Cancel"
        )
        self.cancel_button.setObjectName(
            "dangerButton"
        )
        self.cancel_button.setEnabled(False)

        buttons_layout.addWidget(
            self.analyze_latest_button
        )
        buttons_layout.addWidget(
            self.import_latest_button
        )
        buttons_layout.addStretch()
        buttons_layout.addWidget(
            self.cancel_button
        )

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(
            0,
            100,
        )
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat(
            "%p%"
        )

        self.progress_label = QLabel(
            "Waiting for an operation."
        )
        self.progress_label.setObjectName(
            "mutedLabel"
        )

        operation_layout.addWidget(
            operation_title
        )
        operation_layout.addWidget(
            self.selected_report_label
        )
        operation_layout.addLayout(
            buttons_layout
        )
        operation_layout.addWidget(
            self.progress_bar
        )
        operation_layout.addWidget(
            self.progress_label
        )

        layout.addWidget(operation_card)

        result_card = QFrame()
        result_card.setObjectName("card")

        result_layout = QVBoxLayout(
            result_card
        )
        result_layout.setContentsMargins(
            22,
            20,
            22,
            20,
        )

        result_title = QLabel(
            "Last result"
        )
        result_title.setObjectName(
            "sectionTitle"
        )

        self.result_table = QTableWidget(
            0,
            2,
        )

        self.result_table.setHorizontalHeaderLabels(
            [
                "Field",
                "Value",
            ]
        )

        self.result_table.verticalHeader().setVisible(
            False
        )

        self.result_table.horizontalHeader().setSectionResizeMode(
            0,
            QHeaderView.ResizeMode.ResizeToContents,
        )

        self.result_table.horizontalHeader().setSectionResizeMode(
            1,
            QHeaderView.ResizeMode.Stretch,
        )

        self.result_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )

        self.result_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )

        result_layout.addWidget(result_title)
        result_layout.addWidget(
            self.result_table
        )

        layout.addWidget(
            result_card,
            1,
        )

        return page

    def _create_summary_card(
        self,
        title: str,
        value: str,
    ) -> dict[str, Any]:
        """
        Crea una tarjeta de resumen.
        """

        frame = QFrame()
        frame.setObjectName("summaryCard")

        frame.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )

        frame.setMinimumHeight(115)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(
            18,
            16,
            18,
            16,
        )

        title_label = QLabel(title)
        title_label.setObjectName(
            "cardTitle"
        )

        value_label = QLabel(value)
        value_label.setObjectName(
            "cardValue"
        )

        layout.addWidget(title_label)
        layout.addWidget(value_label)
        layout.addStretch()

        return {
            "frame": frame,
            "title": title_label,
            "value": value_label,
        }

    # =========================================================
    # REPORTS PAGE
    # =========================================================

    def _create_reports_page(self) -> QWidget:
        """
        Crea la página de reportes.
        """

        page = QWidget()

        layout = QVBoxLayout(page)
        layout.setContentsMargins(
            28,
            24,
            28,
            24,
        )
        layout.setSpacing(16)

        header_layout = QHBoxLayout()

        title_container = QVBoxLayout()

        title = QLabel(
            "Pending reports"
        )
        title.setObjectName(
            "sectionTitle"
        )

        subtitle = QLabel(
            "Select a report to preview, analyze or import."
        )
        subtitle.setObjectName(
            "sectionSubtitle"
        )

        title_container.addWidget(title)
        title_container.addWidget(subtitle)

        self.clean_temp_button = QPushButton(
            "Clean temporary files"
        )
        self.clean_temp_button.setObjectName(
            "secondaryButton"
        )

        header_layout.addLayout(
            title_container
        )
        header_layout.addStretch()
        header_layout.addWidget(
            self.clean_temp_button
        )

        layout.addLayout(header_layout)

        reports_content = QHBoxLayout()
        reports_content.setSpacing(16)

        list_card = QFrame()
        list_card.setObjectName("card")

        list_layout = QVBoxLayout(list_card)
        list_layout.setContentsMargins(
            16,
            16,
            16,
            16,
        )

        self.reports_list = QListWidget()

        list_layout.addWidget(
            self.reports_list
        )

        detail_card = QFrame()
        detail_card.setObjectName("card")

        detail_layout = QVBoxLayout(
            detail_card
        )
        detail_layout.setContentsMargins(
            22,
            20,
            22,
            20,
        )
        detail_layout.setSpacing(12)

        detail_title = QLabel(
            "Report details"
        )
        detail_title.setObjectName(
            "sectionTitle"
        )

        self.report_name_label = QLabel(
            "No report selected"
        )
        self.report_name_label.setObjectName(
            "cardValue"
        )

        self.report_path_label = QLabel("-")
        self.report_path_label.setObjectName(
            "mutedLabel"
        )
        self.report_path_label.setWordWrap(True)

        self.report_size_label = QLabel(
            "Size: -"
        )

        self.report_modified_label = QLabel(
            "Modified: -"
        )

        report_buttons_layout = QHBoxLayout()

        self.preview_report_button = QPushButton(
            "Preview"
        )
        self.preview_report_button.setObjectName(
            "secondaryButton"
        )

        self.analyze_report_button = QPushButton(
            "Analyze"
        )
        self.analyze_report_button.setObjectName(
            "secondaryButton"
        )

        self.import_report_button = QPushButton(
            "Import"
        )
        self.import_report_button.setObjectName(
            "primaryButton"
        )

        report_buttons_layout.addWidget(
            self.preview_report_button
        )
        report_buttons_layout.addWidget(
            self.analyze_report_button
        )
        report_buttons_layout.addWidget(
            self.import_report_button
        )

        detail_layout.addWidget(
            detail_title
        )
        detail_layout.addWidget(
            self.report_name_label
        )
        detail_layout.addWidget(
            self.report_path_label
        )
        detail_layout.addSpacing(8)
        detail_layout.addWidget(
            self.report_size_label
        )
        detail_layout.addWidget(
            self.report_modified_label
        )
        detail_layout.addStretch()
        detail_layout.addLayout(
            report_buttons_layout
        )

        reports_content.addWidget(
            list_card,
            2,
        )
        reports_content.addWidget(
            detail_card,
            3,
        )

        layout.addLayout(
            reports_content,
            1,
        )

        return page

    # =========================================================
    # PREVIEW PAGE
    # =========================================================

    def _create_preview_page(self) -> QWidget:
        """
        Crea la página de vista previa.
        """

        page = QWidget()

        layout = QVBoxLayout(page)
        layout.setContentsMargins(
            28,
            24,
            28,
            24,
        )
        layout.setSpacing(16)

        header_layout = QHBoxLayout()

        header_text = QVBoxLayout()

        title = QLabel(
            "Report preview"
        )
        title.setObjectName(
            "sectionTitle"
        )

        self.preview_subtitle = QLabel(
            "No report loaded."
        )
        self.preview_subtitle.setObjectName(
            "sectionSubtitle"
        )

        header_text.addWidget(title)
        header_text.addWidget(
            self.preview_subtitle
        )

        self.preview_valid_only = QCheckBox(
            "Show valid records only"
        )

        header_layout.addLayout(
            header_text
        )
        header_layout.addStretch()
        header_layout.addWidget(
            self.preview_valid_only
        )

        layout.addLayout(header_layout)

        self.preview_table = QTableWidget()
        self.preview_table.setAlternatingRowColors(
            True
        )

        self.preview_table.setColumnCount(
            len(self.PREVIEW_COLUMNS)
        )

        self.preview_table.setHorizontalHeaderLabels(
            [
                label
                for _, label in self.PREVIEW_COLUMNS
            ]
        )

        self.preview_table.verticalHeader().setVisible(
            False
        )

        self.preview_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents
        )

        self.preview_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )

        self.preview_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )

        layout.addWidget(
            self.preview_table,
            1,
        )

        return page

    # =========================================================
    # SETTINGS PAGE
    # =========================================================

    def _create_settings_page(self) -> QWidget:
        """
        Crea la página de configuración.
        """

        page = QWidget()

        layout = QVBoxLayout(page)
        layout.setContentsMargins(
            28,
            24,
            28,
            24,
        )
        layout.setSpacing(16)

        title = QLabel("Settings")
        title.setObjectName("sectionTitle")

        subtitle = QLabel(
            "Configure the visual behavior of MotorTracker."
        )
        subtitle.setObjectName(
            "sectionSubtitle"
        )

        settings_card = QFrame()
        settings_card.setObjectName("card")

        settings_layout = QVBoxLayout(
            settings_card
        )
        settings_layout.setContentsMargins(
            22,
            20,
            22,
            20,
        )
        settings_layout.setSpacing(12)

        theme_label = QLabel(
            "Application theme"
        )
        theme_label.setObjectName(
            "cardTitle"
        )

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(
            [
                "Light",
                "Dark",
            ]
        )

        self.theme_combo.setCurrentText(
            self.current_theme
        )

        self.backup_checkbox = QCheckBox(
            "Create backup before importing"
        )

        self.backup_checkbox.setChecked(
            self._get_backup_setting()
        )

        self.move_processed_checkbox = QCheckBox(
            "Move imported reports to Processed"
        )

        self.move_processed_checkbox.setChecked(
            True
        )

        settings_layout.addWidget(
            theme_label
        )
        settings_layout.addWidget(
            self.theme_combo
        )
        settings_layout.addSpacing(10)
        settings_layout.addWidget(
            self.backup_checkbox
        )
        settings_layout.addWidget(
            self.move_processed_checkbox
        )
        settings_layout.addStretch()

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(
            settings_card
        )
        layout.addStretch()

        return page

    # =========================================================
    # MENU AND STATUS BAR
    # =========================================================

    def _create_status_bar(self) -> None:
        """
        Crea la barra de estado.
        """

        status_bar = QStatusBar()
        self.setStatusBar(status_bar)

        self.status_message_label = QLabel(
            "Ready"
        )

        status_bar.addWidget(
            self.status_message_label
        )

    def _create_menu(self) -> None:
        """
        Crea el menú principal.
        """

        file_menu = self.menuBar().addMenu(
            "File"
        )

        refresh_action = QAction(
            "Refresh",
            self,
        )

        refresh_action.triggered.connect(
            self.refresh_data
        )

        exit_action = QAction(
            "Exit",
            self,
        )

        exit_action.triggered.connect(
            self.close
        )

        file_menu.addAction(
            refresh_action
        )
        file_menu.addSeparator()
        file_menu.addAction(
            exit_action
        )

        view_menu = self.menuBar().addMenu(
            "View"
        )

        light_action = QAction(
            "Light theme",
            self,
        )

        dark_action = QAction(
            "Dark theme",
            self,
        )

        light_action.triggered.connect(
            lambda: self.set_theme("Light")
        )

        dark_action.triggered.connect(
            lambda: self.set_theme("Dark")
        )

        view_menu.addAction(
            light_action
        )
        view_menu.addAction(
            dark_action
        )

    # =========================================================
    # SIGNALS
    # =========================================================

    def _connect_signals(self) -> None:
        """
        Conecta los eventos de la interfaz.
        """

        sidebar_buttons = [
            self.dashboard_button,
            self.reports_button,
            self.preview_button,
            self.settings_button,
        ]

        for button in sidebar_buttons:
            button.clicked.connect(
                lambda checked=False, selected=button:
                self._switch_page(selected)
            )

        self.refresh_button.clicked.connect(
            self.refresh_data
        )

        self.analyze_latest_button.clicked.connect(
            self.analyze_latest_report
        )

        self.import_latest_button.clicked.connect(
            self.import_latest_report
        )

        self.cancel_button.clicked.connect(
            self.cancel_current_operation
        )

        self.reports_list.currentItemChanged.connect(
            self._on_report_selected
        )

        self.preview_report_button.clicked.connect(
            self.preview_selected_report
        )

        self.analyze_report_button.clicked.connect(
            self.analyze_selected_report
        )

        self.import_report_button.clicked.connect(
            self.import_selected_report
        )

        self.clean_temp_button.clicked.connect(
            self.clean_temporary_files
        )

        self.theme_combo.currentTextChanged.connect(
            self.set_theme
        )

        self.preview_valid_only.toggled.connect(
            self._filter_preview_table
        )

    # =========================================================
    # PAGE NAVIGATION
    # =========================================================

    def _switch_page(
        self,
        selected_button: QPushButton,
    ) -> None:
        """
        Cambia la página visible.
        """

        buttons = [
            self.dashboard_button,
            self.reports_button,
            self.preview_button,
            self.settings_button,
        ]

        for button in buttons:
            button.setChecked(
                button is selected_button
            )

        page_index = int(
            selected_button.property(
                "page_index"
            )
        )

        self.pages.setCurrentIndex(
            page_index
        )

        page_data = {
            0: (
                "Dashboard",
                "MotorTracker general status",
            ),
            1: (
                "Reports",
                "Pending Excel reports",
            ),
            2: (
                "Preview",
                "Review report records",
            ),
            3: (
                "Settings",
                "Application preferences",
            ),
        }

        title, subtitle = page_data.get(
            page_index,
            (
                APP_TITLE,
                "",
            ),
        )

        self.page_title.setText(title)
        self.page_subtitle.setText(
            subtitle
        )

    # =========================================================
    # DATA REFRESH
    # =========================================================

    def refresh_data(self) -> None:
        """
        Actualiza el estado general de la interfaz.
        """

        if self._operation_is_running():
            return

        try:
            status = self.service.get_status()

            pending_reports = status.get(
                "pending_reports",
                0,
            )

            database_exists = status.get(
                "database_exists",
                False,
            )

            self.pending_card["value"].setText(
                str(pending_reports)
            )

            self.database_card["value"].setText(
                "Available"
                if database_exists
                else "Not found"
            )

            latest_report = status.get(
                "latest_report",
                "",
            )

            if latest_report:
                self.selected_report_label.setText(
                    Path(latest_report).name
                )
            else:
                self.selected_report_label.setText(
                    "No pending reports"
                )

            self._load_reports_list()

            self._set_status(
                "Data updated.",
                running=False,
            )

        except Exception as error:
            LoggerManager.exception(
                "Could not refresh interface data."
            )

            self._show_error(
                "Refresh error",
                str(error),
            )

    def _load_reports_list(self) -> None:
        """
        Carga la lista de reportes.
        """

        self.reports_list.clear()
        self.current_report = None

        reports_info = (
            self.service.get_pending_reports_info()
        )

        for report_info in reports_info:
            name = str(
                report_info.get(
                    "name",
                    "",
                )
            )

            path = str(
                report_info.get(
                    "path",
                    "",
                )
            )

            item = QListWidgetItem(name)
            item.setData(
                Qt.ItemDataRole.UserRole,
                report_info,
            )

            item.setToolTip(path)

            self.reports_list.addItem(
                item
            )

        has_reports = bool(reports_info)

        self.preview_report_button.setEnabled(
            has_reports
        )
        self.analyze_report_button.setEnabled(
            has_reports
        )
        self.import_report_button.setEnabled(
            has_reports
        )
        self.analyze_latest_button.setEnabled(
            has_reports
        )
        self.import_latest_button.setEnabled(
            has_reports
        )

        if has_reports:
            self.reports_list.setCurrentRow(0)
        else:
            self._clear_report_details()

    # =========================================================
    # REPORT SELECTION
    # =========================================================

    def _on_report_selected(
        self,
        current: QListWidgetItem | None,
        previous: QListWidgetItem | None,
    ) -> None:
        """
        Actualiza la información del reporte seleccionado.
        """

        del previous

        if current is None:
            self.current_report = None
            self._clear_report_details()
            return

        report_info = current.data(
            Qt.ItemDataRole.UserRole
        )

        if not isinstance(
            report_info,
            dict,
        ):
            return

        path = Path(
            str(
                report_info.get(
                    "path",
                    "",
                )
            )
        )

        self.current_report = path

        self.report_name_label.setText(
            str(
                report_info.get(
                    "name",
                    path.name,
                )
            )
        )

        self.report_path_label.setText(
            str(path)
        )

        self.report_size_label.setText(
            f"Size: "
            f"{report_info.get('size_kb', 0)} KB"
        )

        modified = str(
            report_info.get(
                "modified_at",
                "",
            )
        )

        self.report_modified_label.setText(
            f"Modified: {modified or '-'}"
        )

    def _clear_report_details(self) -> None:
        """
        Limpia el panel de detalles.
        """

        self.report_name_label.setText(
            "No report selected"
        )
        self.report_path_label.setText("-")
        self.report_size_label.setText(
            "Size: -"
        )
        self.report_modified_label.setText(
            "Modified: -"
        )

    # =========================================================
    # OPERATIONS
    # =========================================================

    def analyze_latest_report(self) -> None:
        """
        Analiza el reporte más reciente.
        """

        self._start_worker(
            action="analyze_latest",
        )

    def import_latest_report(self) -> None:
        """
        Importa el reporte más reciente.
        """

        if not self._confirm_import():
            return

        self._start_worker(
            action="import_latest",
            move_to_processed=(
                self.move_processed_checkbox.isChecked()
            ),
            create_backup=(
                self.backup_checkbox.isChecked()
            ),
        )

    def preview_selected_report(self) -> None:
        """
        Carga una vista previa del reporte seleccionado.
        """

        report = self._require_selected_report()

        if report is None:
            return

        self._start_worker(
            action="preview_report",
            report_path=report,
        )

    def analyze_selected_report(self) -> None:
        """
        Analiza el reporte seleccionado.
        """

        report = self._require_selected_report()

        if report is None:
            return

        self._start_worker(
            action="analyze_report",
            report_path=report,
        )

    def import_selected_report(self) -> None:
        """
        Importa el reporte seleccionado.
        """

        report = self._require_selected_report()

        if report is None:
            return

        if not self._confirm_import(
            report.name
        ):
            return

        self._start_worker(
            action="import_report",
            report_path=report,
            move_to_processed=(
                self.move_processed_checkbox.isChecked()
            ),
            create_backup=(
                self.backup_checkbox.isChecked()
            ),
        )

    def _start_worker(
        self,
        action: str,
        report_path: Path | None = None,
        move_to_processed: bool = True,
        create_backup: bool | None = None,
    ) -> None:
        """
        Inicia un worker dentro de un QThread.
        """

        if self._operation_is_running():
            self._show_warning(
                "Operation in progress",
                "Wait for the current operation to finish.",
            )
            return

        self.worker_thread = QThread(
            self
        )

        self.worker = ImportWorker(
            action=action,
            report_path=report_path,
            move_to_processed=move_to_processed,
            create_backup=create_backup,
        )

        self.worker.moveToThread(
            self.worker_thread
        )

        self.worker_thread.started.connect(
            self.worker.run
        )

        self.worker.started.connect(
            self._on_worker_started
        )

        self.worker.progress.connect(
            self._on_worker_progress
        )

        self.worker.completed.connect(
            self._on_worker_completed
        )

        self.worker.failed.connect(
            self._on_worker_failed
        )

        self.worker.cancelled.connect(
            self._on_worker_cancelled
        )

        self.worker.finished.connect(
            self.worker_thread.quit
        )

        self.worker.finished.connect(
            self.worker.deleteLater
        )

        self.worker_thread.finished.connect(
            self.worker_thread.deleteLater
        )

        self.worker_thread.finished.connect(
            self._on_thread_finished
        )

        self._set_operation_controls(
            running=True
        )

        self.progress_bar.setValue(0)

        self.worker_thread.start()

    def cancel_current_operation(self) -> None:
        """
        Solicita la cancelación.
        """

        if self.worker is None:
            return

        self.progress_label.setText(
            "Cancelling operation..."
        )

        self.worker.cancel()

    # =========================================================
    # WORKER EVENTS
    # =========================================================

    def _on_worker_started(
        self,
        operation_name: str,
    ) -> None:
        """
        Maneja el inicio del worker.
        """

        self._set_status(
            operation_name,
            running=True,
        )

        self.progress_label.setText(
            operation_name
        )

    def _on_worker_progress(
        self,
        percentage: int,
        stage: str,
        message: str,
        current: int,
        total: int,
    ) -> None:
        """
        Actualiza la barra de progreso.
        """

        self.progress_bar.setValue(
            percentage
        )

        detail = message or stage

        if total > 0:
            detail = (
                f"{detail} "
                f"({current}/{total})"
            )

        self.progress_label.setText(
            detail
        )

        self._set_status(
            detail,
            running=True,
        )

    def _on_worker_completed(
        self,
        result: dict[str, Any],
    ) -> None:
        """
        Procesa una operación exitosa.
        """

        action = str(
            result.get(
                "action",
                "",
            )
        )

        if action in {
            "preview_latest",
            "preview_report",
        }:
            records = result.get(
                "records",
                [],
            )

            if isinstance(records, list):
                self._populate_preview_table(
                    records
                )

                self.preview_subtitle.setText(
                    f"{len(records)} records loaded."
                )

                self._switch_page(
                    self.preview_button
                )

            self._set_status(
                "Preview loaded.",
                running=False,
            )

            return

        self._display_result(result)

        self.progress_bar.setValue(100)
        self.progress_label.setText(
            "Operation completed."
        )

        self._set_status(
            "Operation completed.",
            running=False,
        )

        if action in {
            "import_latest",
            "import_report",
        }:
            self.last_import = result

            QMessageBox.information(
                self,
                "Import completed",
                (
                    f"Imported records: "
                    f"{result.get('imported_records', 0)}\n"
                    f"Duplicates: "
                    f"{result.get('duplicate_records', 0)}\n"
                    f"Invalid records: "
                    f"{result.get('invalid_records', 0)}"
                ),
            )

            self.refresh_data()

        else:
            self.last_analysis = result

            self.new_card["value"].setText(
                str(
                    result.get(
                        "new_records",
                        0,
                    )
                )
            )

            self.duplicate_card["value"].setText(
                str(
                    result.get(
                        "duplicate_records",
                        0,
                    )
                )
            )

    def _on_worker_failed(
        self,
        message: str,
        error_type: str,
    ) -> None:
        """
        Procesa un error del worker.
        """

        self.progress_bar.setObjectName(
            "errorProgress"
        )

        self.progress_bar.style().unpolish(
            self.progress_bar
        )
        self.progress_bar.style().polish(
            self.progress_bar
        )

        self.progress_label.setText(
            message
        )

        self._set_status(
            "Operation failed.",
            running=False,
        )

        full_message = message

        if error_type:
            full_message = (
                f"{error_type}\n\n{message}"
            )

        self._show_error(
            "Operation failed",
            full_message,
        )

    def _on_worker_cancelled(
        self,
        result: dict[str, Any],
    ) -> None:
        """
        Procesa una cancelación.
        """

        self.progress_label.setText(
            "Operation cancelled."
        )

        self._display_result(result)

        self._set_status(
            "Operation cancelled.",
            running=False,
        )

    def _on_thread_finished(self) -> None:
        """
        Limpia referencias del hilo.
        """

        self.worker = None
        self.worker_thread = None

        self._set_operation_controls(
            running=False
        )

    # =========================================================
    # RESULT TABLE
    # =========================================================

    def _display_result(
        self,
        result: dict[str, Any],
    ) -> None:
        """
        Muestra el resultado en la tabla.
        """

        fields = [
            ("success", "Success"),
            ("cancelled", "Cancelled"),
            ("report_path", "Report"),
            ("processed_path", "Processed file"),
            ("database_path", "Database"),
            ("backup_path", "Backup"),
            ("total_records", "Total records"),
            ("valid_records", "Valid records"),
            ("invalid_records", "Invalid records"),
            ("new_records", "New records"),
            ("duplicate_records", "Duplicates"),
            ("imported_records", "Imported records"),
            ("error_records", "Errors"),
            ("duration_seconds", "Duration"),
        ]

        rows: list[tuple[str, Any]] = []

        for key, label in fields:
            if key not in result:
                continue

            value = result.get(key)

            if value in {
                "",
                None,
            }:
                value = "-"

            rows.append(
                (
                    label,
                    value,
                )
            )

        errors = result.get(
            "errors",
            [],
        )

        if errors:
            rows.append(
                (
                    "Error details",
                    "\n".join(
                        str(error)
                        for error in errors
                    ),
                )
            )

        self.result_table.setRowCount(
            len(rows)
        )

        for row_index, (
            label,
            value,
        ) in enumerate(rows):
            label_item = QTableWidgetItem(
                str(label)
            )

            value_item = QTableWidgetItem(
                str(value)
            )

            self.result_table.setItem(
                row_index,
                0,
                label_item,
            )

            self.result_table.setItem(
                row_index,
                1,
                value_item,
            )

        self.result_table.resizeRowsToContents()

    # =========================================================
    # PREVIEW TABLE
    # =========================================================

    def _populate_preview_table(
        self,
        records: list[dict[str, Any]],
    ) -> None:
        """
        Muestra los registros en la tabla de vista previa.
        """

        self.preview_table.setRowCount(
            len(records)
        )

        for row_index, record in enumerate(records):
            is_valid = bool(
                record.get(
                    "is_valid",
                    False,
                )
            )

            for column_index, (
                key,
                _,
            ) in enumerate(
                self.PREVIEW_COLUMNS
            ):
                value = record.get(
                    key,
                    "",
                )

                if isinstance(value, bool):
                    value = (
                        "Yes"
                        if value
                        else "No"
                    )

                item = QTableWidgetItem(
                    str(value or "")
                )

                item.setData(
                    Qt.ItemDataRole.UserRole,
                    is_valid,
                )

                self.preview_table.setItem(
                    row_index,
                    column_index,
                    item,
                )

        self.preview_table.resizeRowsToContents()

        self._filter_preview_table(
            self.preview_valid_only.isChecked()
        )

    def _filter_preview_table(
        self,
        valid_only: bool,
    ) -> None:
        """
        Oculta registros inválidos cuando el filtro está activo.
        """

        for row_index in range(
            self.preview_table.rowCount()
        ):
            first_item = self.preview_table.item(
                row_index,
                0,
            )

            if first_item is None:
                continue

            is_valid = bool(
                first_item.data(
                    Qt.ItemDataRole.UserRole
                )
            )

            self.preview_table.setRowHidden(
                row_index,
                valid_only and not is_valid,
            )

    # =========================================================
    # CLEANUP
    # =========================================================

    def clean_temporary_files(self) -> None:
        """
        Elimina archivos temporales de Excel.
        """

        try:
            deleted = (
                self.service.clean_temporary_files()
            )

            QMessageBox.information(
                self,
                "Temporary files",
                f"Deleted files: {deleted}",
            )

            self.refresh_data()

        except Exception as error:
            self._show_error(
                "Cleanup error",
                str(error),
            )

    # =========================================================
    # THEME
    # =========================================================

    def set_theme(
        self,
        theme: str,
    ) -> None:
        """
        Cambia el tema de la aplicación.
        """

        normalized = normalize_theme(
            theme
        )

        if normalized == self.current_theme:
            return

        self.current_theme = normalized

        self._apply_current_theme()

        self.theme_combo.blockSignals(True)
        self.theme_combo.setCurrentText(
            normalized
        )
        self.theme_combo.blockSignals(False)

        self.theme_changed.emit(
            normalized
        )

    def _apply_current_theme(self) -> None:
        """
        Aplica el tema actual.
        """

        application = QApplication.instance()

        if application is None:
            return

        apply_theme(
            application,
            self.current_theme,
        )

    # =========================================================
    # HELPERS
    # =========================================================

    def _set_operation_controls(
        self,
        running: bool,
    ) -> None:
        """
        Habilita o deshabilita controles durante una operación.
        """

        self.cancel_button.setEnabled(
            running
        )

        controls = [
            self.refresh_button,
            self.analyze_latest_button,
            self.import_latest_button,
            self.preview_report_button,
            self.analyze_report_button,
            self.import_report_button,
            self.clean_temp_button,
        ]

        for control in controls:
            control.setEnabled(
                not running
            )

        self.reports_list.setEnabled(
            not running
        )

    def _set_status(
        self,
        message: str,
        running: bool,
    ) -> None:
        """
        Actualiza los textos de estado.
        """

        self.status_message_label.setText(
            message
        )

        self.top_status_label.setText(
            message
        )

        self.sidebar_status_label.setText(
            "Processing..."
            if running
            else message
        )

    def _operation_is_running(self) -> bool:
        """
        Indica si existe un worker activo.
        """

        return (
            self.worker_thread is not None
            and self.worker_thread.isRunning()
        )

    def _require_selected_report(
        self,
    ) -> Path | None:
        """
        Valida que exista un reporte seleccionado.
        """

        if self.current_report is None:
            self._show_warning(
                "No report selected",
                "Select a report first.",
            )

            return None

        return self.current_report

    def _confirm_import(
        self,
        filename: str | None = None,
    ) -> bool:
        """
        Solicita confirmación antes de importar.
        """

        report_name = (
            filename
            or "the latest pending report"
        )

        response = QMessageBox.question(
            self,
            "Confirm import",
            (
                f"Import {report_name}?\n\n"
                "New records will be added to the database."
            ),
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        return (
            response
            == QMessageBox.StandardButton.Yes
        )

    def _get_backup_setting(self) -> bool:
        """
        Obtiene la configuración inicial del backup.
        """

        value = self.config.get(
            "database.backup",
            True,
        )

        if isinstance(value, bool):
            return value

        return str(value).strip().lower() in {
            "true",
            "1",
            "yes",
            "si",
            "sí",
        }

    def _show_error(
        self,
        title: str,
        message: str,
    ) -> None:
        """
        Muestra un error.
        """

        QMessageBox.critical(
            self,
            title,
            message,
        )

    def _show_warning(
        self,
        title: str,
        message: str,
    ) -> None:
        """
        Muestra una advertencia.
        """

        QMessageBox.warning(
            self,
            title,
            message,
        )

    # =========================================================
    # CLOSE EVENT
    # =========================================================

    def closeEvent(
        self,
        event: QCloseEvent,
    ) -> None:
        """
        Controla el cierre de la ventana.
        """

        if self._operation_is_running():
            response = QMessageBox.question(
                self,
                "Operation in progress",
                (
                    "An operation is currently running.\n"
                    "Do you want to cancel it and exit?"
                ),
                QMessageBox.StandardButton.Yes
                | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )

            if (
                response
                == QMessageBox.StandardButton.No
            ):
                event.ignore()
                return

            if self.worker is not None:
                self.worker.cancel()

            if self.worker_thread is not None:
                self.worker_thread.quit()
                self.worker_thread.wait(
                    3000
                )

        event.accept()