"""
app/utils/file_manager.py

MotorTracker
Administración de archivos, carpetas, reportes,
base de datos y copias de seguridad.
"""

from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

from app.core.config_manager import ConfigManager
from app.core.exceptions import (
    BackupError,
    DatabaseNotFoundError,
    FileManagerError,
    InvalidFileExtensionError,
    ReportNotFoundError,
    ReportReadError,
)


class FileManager:
    """
    Centraliza las operaciones relacionadas con archivos.

    Responsabilidades:

    - Localizar la base de datos.
    - Detectar reportes pendientes.
    - Validar archivos Excel.
    - Mover reportes procesados.
    - Crear copias de seguridad.
    - Crear las carpetas necesarias.
    - Eliminar archivos temporales de Excel.
    """

    DEFAULT_EXCEL_EXTENSIONS = (
        ".xlsx",
        ".xlsm",
        ".xls",
    )

    def __init__(
        self,
        config: ConfigManager | None = None,
    ) -> None:
        """
        Inicializa las rutas configuradas para MotorTracker.

        Args:
            config:
                Instancia opcional de ConfigManager. Esto facilita
                las pruebas unitarias y la inyección de configuración.
        """

        self.config = config or ConfigManager()

        self.database_folder = self._get_configured_path(
            key="database.folder",
            default="Database",
        )

        database_filename = self.config.get(
            "database.file",
            "MASTER TRACK MOTORES.xlsx",
        )

        self.database_file = (
            self.database_folder / str(database_filename)
        )

        self.reports_folder = self._get_configured_path(
            key="reports.folder",
            default="Reports",
        )

        self.processed_folder = self._get_configured_path(
            key="reports.processed_folder",
            default="Processed",
        )

        self.logs_folder = self._get_configured_path(
            key="logs.folder",
            default="Logs",
        )

        self.backup_folder = self._get_configured_path(
            key="database.backup_folder",
            default="Backups",
        )

        self.create_folders()

    # =========================================================
    # DATABASE
    # =========================================================

    def database_exists(self) -> bool:
        """
        Indica si la base de datos existe.
        """

        return (
            self.database_file.exists()
            and self.database_file.is_file()
        )

    def get_database_path(self) -> Path:
        """
        Devuelve la ruta de la base de datos.

        Raises:
            DatabaseNotFoundError:
                Cuando el archivo no existe.
        """

        if not self.database_exists():
            raise DatabaseNotFoundError(
                "No se encontró la base de datos: "
                f"{self.database_file}"
            )

        return self.database_file

    def set_database_path(
        self,
        database_path: Path | str,
    ) -> None:
        """
        Cambia temporalmente la ruta de la base de datos.

        No modifica automáticamente config.json.

        Args:
            database_path:
                Nueva ruta del archivo Excel.
        """

        path = Path(database_path).expanduser()

        self.database_folder = path.parent
        self.database_file = path

    # =========================================================
    # REPORTS
    # =========================================================

    def get_reports(self) -> list[Path]:
        """
        Devuelve los reportes Excel pendientes.

        Los archivos se ordenan del más reciente al más antiguo.
        Se ignoran los archivos temporales generados por Excel.
        """

        self.reports_folder.mkdir(
            parents=True,
            exist_ok=True,
        )

        extensions = self.get_allowed_extensions()
        reports: list[Path] = []

        try:
            for file in self.reports_folder.iterdir():
                if not file.is_file():
                    continue

                if self.is_temporary_excel_file(file):
                    continue

                if file.suffix.lower() not in extensions:
                    continue

                reports.append(file)

            reports.sort(
                key=lambda item: item.stat().st_mtime,
                reverse=True,
            )

            return reports

        except PermissionError as error:
            raise FileManagerError(
                "No se pudo acceder a la carpeta de reportes. "
                "Verifica los permisos de la carpeta."
            ) from error

        except OSError as error:
            raise FileManagerError(
                f"No fue posible consultar los reportes: {error}"
            ) from error

    def get_latest_report(self) -> Path:
        """
        Devuelve el reporte pendiente más reciente.

        Raises:
            ReportNotFoundError:
                Cuando la carpeta Reports no contiene reportes.
        """

        reports = self.get_reports()

        if not reports:
            raise ReportNotFoundError(
                "No se encontraron reportes pendientes en: "
                f"{self.reports_folder}"
            )

        return reports[0]

    def reports_count(self) -> int:
        """
        Devuelve la cantidad de reportes pendientes.
        """

        return len(self.get_reports())

    def report_exists(
        self,
        filename: str,
    ) -> bool:
        """
        Comprueba si un reporte existe en la carpeta Reports.
        """

        if not filename:
            return False

        report_path = self.reports_folder / filename

        return report_path.exists() and report_path.is_file()

    def get_report_path(
        self,
        filename: str,
    ) -> Path:
        """
        Devuelve la ruta de un reporte específico.

        Raises:
            ReportNotFoundError:
                Cuando el reporte no existe.
        """

        report_path = self.reports_folder / filename

        if not report_path.exists() or not report_path.is_file():
            raise ReportNotFoundError(
                f"No se encontró el reporte: {report_path}"
            )

        return report_path

    # =========================================================
    # MOVE
    # =========================================================

    def move_to_processed(
        self,
        report: Path | str,
    ) -> Path:
        """
        Mueve un reporte correctamente procesado a Processed.

        El archivo recibe un prefijo con fecha y hora para evitar
        sobrescribir reportes anteriores con el mismo nombre.

        Args:
            report:
                Ruta del reporte que será movido.

        Returns:
            Ruta final del reporte procesado.
        """

        report_path = Path(report)

        if not report_path.exists():
            raise ReportNotFoundError(
                f"No se encontró el reporte que se desea mover: "
                f"{report_path}"
            )

        if not report_path.is_file():
            raise ReportNotFoundError(
                "La ruta del reporte no corresponde a un archivo."
            )

        self.processed_folder.mkdir(
            parents=True,
            exist_ok=True,
        )

        timestamp = datetime.now().strftime(
            "%Y%m%d_%H%M%S"
        )

        destination = (
            self.processed_folder
            / f"{timestamp}_{report_path.name}"
        )

        destination = self._get_unique_path(destination)

        try:
            shutil.move(
                str(report_path),
                str(destination),
            )

            return destination

        except PermissionError as error:
            raise FileManagerError(
                "No fue posible mover el reporte. "
                "Verifica que no esté abierto en Excel."
            ) from error

        except OSError as error:
            raise FileManagerError(
                f"No fue posible mover el reporte procesado: {error}"
            ) from error

    def processed_exists(
        self,
        filename: str,
    ) -> bool:
        """
        Comprueba si un archivo existe en Processed.
        """

        if not filename:
            return False

        processed_path = self.processed_folder / filename

        return (
            processed_path.exists()
            and processed_path.is_file()
        )

    # =========================================================
    # BACKUP
    # =========================================================

    def backup_database(self) -> Path:
        """
        Crea una copia de seguridad de la base de datos.

        Conserva el nombre y la extensión original del archivo.

        Returns:
            Ruta del backup creado.
        """

        database_path = self.get_database_path()

        self.backup_folder.mkdir(
            parents=True,
            exist_ok=True,
        )

        timestamp = datetime.now().strftime(
            "%Y%m%d_%H%M%S_%f"
        )

        backup_name = (
            f"{database_path.stem}_"
            f"{timestamp}"
            f"{database_path.suffix}"
        )

        backup_path = self.backup_folder / backup_name

        try:
            shutil.copy2(
                database_path,
                backup_path,
            )

            return backup_path

        except PermissionError as error:
            raise BackupError(
                "No fue posible crear el backup. "
                "Verifica los permisos de la carpeta."
            ) from error

        except OSError as error:
            raise BackupError(
                f"No fue posible crear el backup: {error}"
            ) from error

    # =========================================================
    # VALIDATION
    # =========================================================

    def validate_excel(
        self,
        file: Path | str,
    ) -> bool:
        """
        Valida que una ruta corresponda a un archivo Excel válido.

        Esta validación comprueba:

        - Que la ruta exista.
        - Que sea un archivo.
        - Que no sea un archivo temporal de Excel.
        - Que tenga una extensión permitida.
        - Que no esté completamente vacío.

        Args:
            file:
                Ruta del archivo que será validado.

        Returns:
            True cuando el archivo supera las validaciones.
        """

        file_path = Path(file)

        if not file_path.exists():
            raise ReportNotFoundError(
                f"No se encontró el archivo Excel: {file_path}"
            )

        if not file_path.is_file():
            raise ReportNotFoundError(
                "La ruta indicada no corresponde a un archivo."
            )

        if self.is_temporary_excel_file(file_path):
            raise ReportReadError(
                "No se puede importar un archivo temporal de Excel. "
                "Cierra el archivo original y vuelve a intentarlo."
            )

        extensions = self.get_allowed_extensions()

        if file_path.suffix.lower() not in extensions:
            allowed = ", ".join(
                sorted(extensions)
            )

            raise InvalidFileExtensionError(
                f"Extensión no permitida: {file_path.suffix}. "
                f"Extensiones aceptadas: {allowed}"
            )

        try:
            if file_path.stat().st_size <= 0:
                raise ReportReadError(
                    f"El archivo está vacío: {file_path.name}"
                )

        except OSError as error:
            raise ReportReadError(
                f"No fue posible inspeccionar el archivo: {error}"
            ) from error

        return True

    def get_allowed_extensions(self) -> tuple[str, ...]:
        """
        Devuelve las extensiones Excel configuradas y normalizadas.
        """

        configured_extensions = self.config.get(
            "reports.extensions",
            list(self.DEFAULT_EXCEL_EXTENSIONS),
        )

        if not configured_extensions:
            configured_extensions = list(
                self.DEFAULT_EXCEL_EXTENSIONS
            )

        if isinstance(configured_extensions, str):
            configured_extensions = [
                configured_extensions
            ]

        normalized_extensions: list[str] = []

        for extension in configured_extensions:
            normalized = str(extension).strip().lower()

            if not normalized:
                continue

            if not normalized.startswith("."):
                normalized = f".{normalized}"

            if normalized not in normalized_extensions:
                normalized_extensions.append(normalized)

        if not normalized_extensions:
            return self.DEFAULT_EXCEL_EXTENSIONS

        return tuple(normalized_extensions)

    @staticmethod
    def is_temporary_excel_file(
        file: Path | str,
    ) -> bool:
        """
        Detecta archivos temporales creados por Microsoft Excel.
        """

        file_path = Path(file)

        return file_path.name.startswith("~$")

    # =========================================================
    # FILE INFORMATION
    # =========================================================

    @staticmethod
    def file_size(
        file: Path | str,
    ) -> float:
        """
        Devuelve el tamaño del archivo en kilobytes.
        """

        file_path = Path(file)

        if not file_path.exists():
            raise FileManagerError(
                f"No se encontró el archivo: {file_path}"
            )

        return round(
            file_path.stat().st_size / 1024,
            2,
        )

    @staticmethod
    def modified_date(
        file: Path | str,
    ) -> datetime:
        """
        Devuelve la fecha de última modificación.
        """

        file_path = Path(file)

        if not file_path.exists():
            raise FileManagerError(
                f"No se encontró el archivo: {file_path}"
            )

        return datetime.fromtimestamp(
            file_path.stat().st_mtime
        )

    @staticmethod
    def created_date(
        file: Path | str,
    ) -> datetime:
        """
        Devuelve la fecha de creación registrada por el sistema.
        """

        file_path = Path(file)

        if not file_path.exists():
            raise FileManagerError(
                f"No se encontró el archivo: {file_path}"
            )

        return datetime.fromtimestamp(
            file_path.stat().st_ctime
        )

    @classmethod
    def file_info(
        cls,
        file: Path | str,
    ) -> dict[str, Any]:
        """
        Devuelve información general de un archivo.
        """

        file_path = Path(file)

        if not file_path.exists():
            raise FileManagerError(
                f"No se encontró el archivo: {file_path}"
            )

        return {
            "name": file_path.name,
            "stem": file_path.stem,
            "extension": file_path.suffix.lower(),
            "path": str(file_path),
            "absolute_path": str(file_path.resolve()),
            "size_kb": cls.file_size(file_path),
            "created_at": cls.created_date(
                file_path
            ).isoformat(),
            "modified_at": cls.modified_date(
                file_path
            ).isoformat(),
        }

    # =========================================================
    # DELETE AND CLEANUP
    # =========================================================

    @staticmethod
    def delete_file(
        file: Path | str,
    ) -> bool:
        """
        Elimina un archivo.

        Returns:
            True si el archivo fue eliminado.
            False si el archivo no existía.
        """

        file_path = Path(file)

        if not file_path.exists():
            return False

        if not file_path.is_file():
            raise FileManagerError(
                "La ruta indicada no corresponde a un archivo."
            )

        try:
            file_path.unlink()
            return True

        except PermissionError as error:
            raise FileManagerError(
                "No fue posible eliminar el archivo. "
                "Verifica que no esté abierto."
            ) from error

        except OSError as error:
            raise FileManagerError(
                f"No fue posible eliminar el archivo: {error}"
            ) from error

    def clean_temp_files(self) -> int:
        """
        Elimina archivos temporales de Excel dentro de Reports.

        Returns:
            Cantidad de archivos temporales eliminados.
        """

        self.reports_folder.mkdir(
            parents=True,
            exist_ok=True,
        )

        deleted = 0

        for file in self.reports_folder.iterdir():
            if not file.is_file():
                continue

            if not self.is_temporary_excel_file(file):
                continue

            try:
                file.unlink()
                deleted += 1

            except OSError:
                # Un archivo temporal puede seguir bloqueado por Excel.
                # La limpieza continúa con el resto de archivos.
                continue

        return deleted

    # =========================================================
    # DIRECTORY CREATION
    # =========================================================

    def create_folders(self) -> None:
        """
        Crea todas las carpetas necesarias para MotorTracker.
        """

        folders = (
            self.database_folder,
            self.reports_folder,
            self.processed_folder,
            self.logs_folder,
            self.backup_folder,
        )

        try:
            for folder in folders:
                folder.mkdir(
                    parents=True,
                    exist_ok=True,
                )

        except PermissionError as error:
            raise FileManagerError(
                "No fue posible crear las carpetas del sistema. "
                "Verifica los permisos de escritura."
            ) from error

        except OSError as error:
            raise FileManagerError(
                f"No fue posible crear las carpetas: {error}"
            ) from error

    # =========================================================
    # SUMMARY
    # =========================================================

    def summary(self) -> dict[str, Any]:
        """
        Devuelve un resumen del estado de archivos y carpetas.
        """

        reports = self.get_reports()

        return {
            "database": self.database_exists(),
            "database_exists": self.database_exists(),
            "reports": len(reports),
            "pending_reports": len(reports),
            "database_path": str(self.database_file),
            "reports_path": str(self.reports_folder),
            "processed_path": str(self.processed_folder),
            "logs_path": str(self.logs_folder),
            "backup_path": str(self.backup_folder),
            "latest_report": (
                str(reports[0])
                if reports
                else ""
            ),
            "allowed_extensions": list(
                self.get_allowed_extensions()
            ),
        }

    # =========================================================
    # INTERNAL HELPERS
    # =========================================================

    def _get_configured_path(
        self,
        key: str,
        default: str,
    ) -> Path:
        """
        Obtiene y normaliza una ruta desde la configuración.
        """

        configured_value = self.config.get(
            key,
            default,
        )

        if configured_value is None:
            configured_value = default

        configured_text = str(configured_value).strip()

        if not configured_text:
            configured_text = default

        return Path(configured_text).expanduser()

    @staticmethod
    def _get_unique_path(
        desired_path: Path,
    ) -> Path:
        """
        Evita sobrescribir un archivo cuando ya existe otro
        con el mismo nombre.
        """

        if not desired_path.exists():
            return desired_path

        counter = 1

        while True:
            candidate = (
                desired_path.parent
                / (
                    f"{desired_path.stem}_"
                    f"{counter}"
                    f"{desired_path.suffix}"
                )
            )

            if not candidate.exists():
                return candidate

            counter += 1