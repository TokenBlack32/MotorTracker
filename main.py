"""
main.py

MotorTracker
Punto de entrada principal de la aplicación.
"""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMessageBox

from app.core.config_manager import ConfigManager
from app.ui.main_window import MainWindow
from app.ui.styles import (
    APP_TITLE,
    DEFAULT_THEME,
    apply_theme,
    normalize_theme,
)
from app.utils.file_manager import FileManager
from app.utils.logger import LoggerManager


def get_project_root() -> Path:
    """
    Devuelve la carpeta raíz de MotorTracker.

    Funciona tanto al ejecutar el proyecto desde Python como
    cuando posteriormente se genere el EXE con PyInstaller.
    """

    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent

    return Path(__file__).resolve().parent


def configure_working_directory() -> Path:
    """
    Configura la carpeta raíz como directorio de trabajo.

    Esto permite que rutas relativas como Database, Reports,
    Processed, Backups y Logs funcionen correctamente.
    """

    project_root = get_project_root()

    try:
        import os

        os.chdir(project_root)

    except OSError as error:
        raise RuntimeError(
            f"No fue posible acceder a la carpeta del proyecto: "
            f"{project_root}"
        ) from error

    return project_root


def configure_application(
    application: QApplication,
) -> None:
    """
    Configura la identidad y el comportamiento general de Qt.
    """

    application.setApplicationName(APP_TITLE)
    application.setApplicationDisplayName(APP_TITLE)
    application.setOrganizationName("MotorTracker")
    application.setOrganizationDomain("motortracker.local")

    application.setQuitOnLastWindowClosed(True)


def apply_configured_theme(
    application: QApplication,
    config: ConfigManager,
) -> str:
    """
    Obtiene el tema desde config.json y lo aplica.
    """

    configured_theme = config.get(
        "ui.theme",
        DEFAULT_THEME,
    )

    theme = normalize_theme(configured_theme)

    apply_theme(
        application,
        theme,
    )

    return theme


def configure_icon(
    application: QApplication,
    project_root: Path,
) -> None:
    """
    Configura el icono de la aplicación cuando existe.

    Las rutas que se revisan son:

    assets/icons/motortracker.ico
    assets/icons/motortracker.png
    assets/motortracker.ico
    assets/motortracker.png
    """

    icon_candidates = [
        project_root
        / "assets"
        / "icons"
        / "motortracker.ico",

        project_root
        / "assets"
        / "icons"
        / "motortracker.png",

        project_root
        / "assets"
        / "motortracker.ico",

        project_root
        / "assets"
        / "motortracker.png",
    ]

    for icon_path in icon_candidates:
        if not icon_path.exists():
            continue

        icon = QIcon(str(icon_path))

        if icon.isNull():
            continue

        application.setWindowIcon(icon)
        return


def prepare_folders() -> None:
    """
    Crea las carpetas requeridas por MotorTracker.
    """

    file_manager = FileManager()
    file_manager.create_folders()


def show_startup_error(
    application: QApplication,
    error: Exception,
) -> None:
    """
    Muestra un error crítico cuando la aplicación no puede iniciar.
    """

    LoggerManager.exception(
        "MotorTracker no pudo iniciar."
    )

    QMessageBox.critical(
        None,
        "MotorTracker startup error",
        (
            "MotorTracker could not start.\n\n"
            f"{error.__class__.__name__}: {error}"
        ),
    )

    application.quit()


def main() -> int:
    """
    Inicia MotorTracker.

    Returns:
        Código de salida del proceso.
    """

    project_root = configure_working_directory()

    application = QApplication(
        sys.argv
    )

    configure_application(
        application
    )

    try:
        config = ConfigManager()

        apply_configured_theme(
            application,
            config,
        )

        configure_icon(
            application,
            project_root,
        )

        prepare_folders()

        LoggerManager.info(
            "================================"
        )
        LoggerManager.info(
            "MotorTracker iniciado."
        )
        LoggerManager.info(
            f"Directorio: {project_root}"
        )
        LoggerManager.info(
            "================================"
        )

        window = MainWindow()
        window.show()

        exit_code = application.exec()

        LoggerManager.info(
            f"MotorTracker finalizado. Código: {exit_code}"
        )

        return exit_code

    except Exception as error:
        show_startup_error(
            application,
            error,
        )

        return 1


if __name__ == "__main__":
    raise SystemExit(main())