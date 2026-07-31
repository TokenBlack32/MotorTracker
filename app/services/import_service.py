"""
app/services/import_service.py

MotorTracker
Servicio de alto nivel para controlar las importaciones.

La interfaz gráfica, la consola y otros componentes deben usar
ImportService en lugar de acceder directamente a ImportEngine,
ReportReader, DatabaseReader o DatabaseWriter.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from app.core.exceptions import (
    ImportErrorMT,
    ReportNotFoundError,
)
from app.importers.import_engine import (
    ImportEngine,
    ImportProgress,
    ImportResult,
)
from app.models.motor_record import MotorRecord
from app.utils.file_manager import FileManager
from app.utils.logger import LoggerManager


ProgressCallback = Callable[[ImportProgress], None]


class ImportService:
    """
    Expone las operaciones de importación de MotorTracker.

    Responsabilidades:

    - Consultar reportes pendientes.
    - Analizar reportes sin modificar la base.
    - Importar el reporte más reciente.
    - Importar un reporte específico.
    - Mostrar una vista previa.
    - Cancelar una importación.
    - Entregar información de progreso a la interfaz.
    """

    def __init__(
        self,
        file_manager: FileManager | None = None,
        progress_callback: ProgressCallback | None = None,
    ) -> None:
        """
        Inicializa el servicio.

        Args:
            file_manager:
                Administrador de archivos opcional.

            progress_callback:
                Función que recibirá actualizaciones de progreso.
        """

        self.file_manager = file_manager or FileManager()

        self._progress_callback = progress_callback
        self._last_progress: ImportProgress | None = None
        self._last_result: ImportResult | None = None

        self.engine = ImportEngine(
            file_manager=self.file_manager,
            progress_callback=self._handle_progress,
        )

    # =========================================================
    # PROPERTIES
    # =========================================================

    @property
    def is_running(self) -> bool:
        """
        Indica si hay una importación en ejecución.
        """

        return self.engine.is_running

    @property
    def last_progress(self) -> ImportProgress | None:
        """
        Devuelve el último estado de progreso recibido.
        """

        return self._last_progress

    @property
    def last_result(self) -> ImportResult | None:
        """
        Devuelve el resultado de la última operación.
        """

        return self._last_result

    # =========================================================
    # CALLBACK
    # =========================================================

    def set_progress_callback(
        self,
        callback: ProgressCallback | None,
    ) -> None:
        """
        Configura una función para recibir el progreso.

        La función debe aceptar un objeto ImportProgress.

        Ejemplo:

            def on_progress(progress):
                print(progress.message)

            service.set_progress_callback(on_progress)
        """

        self._progress_callback = callback

    def clear_progress_callback(self) -> None:
        """
        Elimina el callback de progreso actual.
        """

        self._progress_callback = None

    # =========================================================
    # REPORT QUERIES
    # =========================================================

    def get_pending_reports(self) -> list[Path]:
        """
        Devuelve los reportes pendientes, ordenados del más
        reciente al más antiguo.
        """

        return self.file_manager.get_reports()

    def get_pending_reports_info(self) -> list[dict[str, Any]]:
        """
        Devuelve información detallada de los reportes pendientes.
        """

        reports_info: list[dict[str, Any]] = []

        for report in self.get_pending_reports():
            try:
                reports_info.append(
                    self.file_manager.file_info(report)
                )

            except Exception as error:
                LoggerManager.warning(
                    f"No fue posible obtener información de "
                    f"{report.name}: {error}"
                )

                reports_info.append(
                    {
                        "name": report.name,
                        "path": str(report),
                        "absolute_path": str(
                            report.resolve()
                        ),
                        "size_kb": 0,
                        "created_at": "",
                        "modified_at": "",
                        "error": str(error),
                    }
                )

        return reports_info

    def get_latest_report(self) -> Path:
        """
        Devuelve el reporte pendiente más reciente.
        """

        return self.file_manager.get_latest_report()

    def pending_reports_count(self) -> int:
        """
        Devuelve el número de reportes pendientes.
        """

        return self.file_manager.reports_count()

    def has_pending_reports(self) -> bool:
        """
        Indica si existen reportes pendientes.
        """

        return self.pending_reports_count() > 0

    # =========================================================
    # PREVIEW
    # =========================================================

    def preview_latest_report(self) -> list[MotorRecord]:
        """
        Devuelve los registros del reporte más reciente sin
        modificar la base de datos.
        """

        report_path = self.get_latest_report()

        return self.preview_report(report_path)

    def preview_report(
        self,
        report_path: Path | str,
    ) -> list[MotorRecord]:
        """
        Lee un reporte y devuelve objetos MotorRecord.

        Esta operación no escribe en la base, no crea backups
        y no mueve el reporte a Processed.
        """

        path = self._resolve_report_path(report_path)

        LoggerManager.info(
            f"Generando vista previa de: {path.name}"
        )

        records = self.engine.preview_report(path)

        LoggerManager.info(
            f"Registros en vista previa: {len(records)}"
        )

        return records

    def preview_report_as_dicts(
        self,
        report_path: Path | str,
    ) -> list[dict[str, Any]]:
        """
        Devuelve la vista previa como una lista de diccionarios.

        Este formato será útil para mostrar registros en tablas
        dentro de la interfaz gráfica.
        """

        records = self.preview_report(report_path)

        return [
            self._record_to_preview_dict(record)
            for record in records
        ]

    # =========================================================
    # ANALYSIS
    # =========================================================

    def analyze_latest_report(self) -> ImportResult:
        """
        Analiza el reporte más reciente sin modificar archivos.
        """

        report_path = self.get_latest_report()

        return self.analyze_report(report_path)

    def analyze_report(
        self,
        report_path: Path | str,
    ) -> ImportResult:
        """
        Detecta registros nuevos, inválidos y duplicados.

        La operación no escribe en la base y no mueve el reporte.
        """

        if self.is_running:
            raise ImportErrorMT(
                "No se puede analizar otro reporte mientras "
                "hay una importación en ejecución."
            )

        path = self._resolve_report_path(report_path)

        LoggerManager.info(
            f"Analizando reporte: {path.name}"
        )

        result = self.engine.analyze_report(path)

        self._last_result = result

        return result

    # =========================================================
    # IMPORT
    # =========================================================

    def import_latest_report(
        self,
        move_to_processed: bool = True,
        create_backup: bool | None = None,
    ) -> ImportResult:
        """
        Importa el reporte pendiente más reciente.

        Args:
            move_to_processed:
                Mueve el reporte a Processed cuando la operación
                termina correctamente.

            create_backup:
                Controla la creación de backup. Cuando es None,
                utiliza el valor de config.json.
        """

        if self.is_running:
            raise ImportErrorMT(
                "Ya existe una importación en ejecución."
            )

        backup_enabled = self._resolve_backup_setting(
            create_backup
        )

        LoggerManager.info(
            "Iniciando importación del reporte más reciente."
        )

        result = self.engine.import_latest_report(
            move_to_processed=move_to_processed,
            create_backup=backup_enabled,
        )

        self._last_result = result

        return result

    def import_report(
        self,
        report_path: Path | str,
        move_to_processed: bool = True,
        create_backup: bool | None = None,
    ) -> ImportResult:
        """
        Importa un reporte específico.

        Args:
            report_path:
                Ruta completa o nombre de un reporte ubicado
                dentro de la carpeta Reports.

            move_to_processed:
                Mueve el reporte después de una importación
                exitosa.

            create_backup:
                Cuando es None, utiliza database.backup de
                config.json.
        """

        if self.is_running:
            raise ImportErrorMT(
                "Ya existe una importación en ejecución."
            )

        path = self._resolve_report_path(report_path)

        backup_enabled = self._resolve_backup_setting(
            create_backup
        )

        LoggerManager.info(
            f"Iniciando importación: {path.name}"
        )

        result = self.engine.import_report(
            report_path=path,
            move_to_processed=move_to_processed,
            create_backup=backup_enabled,
        )

        self._last_result = result

        return result

    def cancel_import(self) -> bool:
        """
        Solicita la cancelación de la importación actual.

        Returns:
            True cuando había una importación ejecutándose.
            False cuando no existía una importación activa.
        """

        if not self.is_running:
            return False

        self.engine.cancel()

        return True

    # =========================================================
    # CLEANUP
    # =========================================================

    def clean_temporary_files(self) -> int:
        """
        Elimina archivos temporales de Excel en Reports.
        """

        deleted_files = self.file_manager.clean_temp_files()

        LoggerManager.info(
            f"Archivos temporales eliminados: {deleted_files}"
        )

        return deleted_files

    # =========================================================
    # STATUS
    # =========================================================

    def get_status(self) -> dict[str, Any]:
        """
        Devuelve el estado general del servicio.
        """

        file_summary = self.file_manager.summary()

        progress_data: dict[str, Any] | None = None

        if self._last_progress is not None:
            progress_data = {
                "stage": self._last_progress.stage,
                "message": self._last_progress.message,
                "current": self._last_progress.current,
                "total": self._last_progress.total,
                "percentage": self._last_progress.percentage,
            }

        result_data: dict[str, Any] | None = None

        if self._last_result is not None:
            result_data = self._last_result.to_dict()

        return {
            "is_running": self.is_running,
            "pending_reports": (
                file_summary.get(
                    "pending_reports",
                    file_summary.get("reports", 0),
                )
            ),
            "database_exists": file_summary.get(
                "database_exists",
                file_summary.get("database", False),
            ),
            "database_path": file_summary.get(
                "database_path",
                "",
            ),
            "reports_path": file_summary.get(
                "reports_path",
                "",
            ),
            "processed_path": file_summary.get(
                "processed_path",
                "",
            ),
            "backup_path": file_summary.get(
                "backup_path",
                "",
            ),
            "latest_report": file_summary.get(
                "latest_report",
                "",
            ),
            "progress": progress_data,
            "last_result": result_data,
        }

    def get_last_result_summary(self) -> dict[str, Any]:
        """
        Devuelve un resumen simplificado de la última operación.
        """

        if self._last_result is None:
            return {
                "available": False,
                "message": (
                    "Todavía no se ha ejecutado una importación."
                ),
            }

        result = self._last_result

        return {
            "available": True,
            "success": result.success,
            "cancelled": result.cancelled,
            "total_records": result.total_records,
            "valid_records": result.valid_records,
            "invalid_records": result.invalid_records,
            "new_records": result.new_records,
            "duplicate_records": result.duplicate_records,
            "imported_records": result.imported_records,
            "error_records": result.error_records,
            "duration_seconds": result.duration_seconds,
            "errors": list(result.errors),
        }

    # =========================================================
    # INTERNAL CALLBACK
    # =========================================================

    def _handle_progress(
        self,
        progress: ImportProgress,
    ) -> None:
        """
        Recibe el progreso del motor y lo reenvía a la interfaz.
        """

        self._last_progress = progress

        if self._progress_callback is None:
            return

        try:
            self._progress_callback(progress)

        except Exception:
            LoggerManager.exception(
                "El callback de progreso del servicio "
                "produjo un error."
            )

    # =========================================================
    # INTERNAL HELPERS
    # =========================================================

    def _resolve_report_path(
        self,
        report_path: Path | str,
    ) -> Path:
        """
        Resuelve una ruta de reporte.

        Permite recibir:

        - Una ruta absoluta.
        - Una ruta relativa existente.
        - Solamente el nombre de un archivo ubicado en Reports.
        """

        path = Path(report_path).expanduser()

        if path.exists() and path.is_file():
            self.file_manager.validate_excel(path)
            return path

        report_in_folder = (
            self.file_manager.reports_folder / path.name
        )

        if (
            report_in_folder.exists()
            and report_in_folder.is_file()
        ):
            self.file_manager.validate_excel(
                report_in_folder
            )

            return report_in_folder

        raise ReportNotFoundError(
            f"No se encontró el reporte: {report_path}"
        )

    def _resolve_backup_setting(
        self,
        create_backup: bool | None,
    ) -> bool:
        """
        Obtiene el valor de configuración para los backups.
        """

        if create_backup is not None:
            return bool(create_backup)

        configured_value = self.file_manager.config.get(
            "database.backup",
            True,
        )

        if isinstance(configured_value, bool):
            return configured_value

        if isinstance(configured_value, str):
            return configured_value.strip().lower() in {
                "true",
                "1",
                "yes",
                "y",
                "si",
                "sí",
            }

        return bool(configured_value)

    @staticmethod
    def _record_to_preview_dict(
        record: MotorRecord,
    ) -> dict[str, Any]:
        """
        Convierte un MotorRecord al formato de vista previa.
        """

        return {
            "model": record.model,
            "part_number": record.part_number,
            "supplier": record.supplier,
            "traceability": record.traceability,
            "no_motors": record.no_motors,
            "vin": record.vin,
            "nct": record.nct,
            "sda": record.sda,
            "rma": record.rma,
            "dtc": record.dtc,
            "issue": record.issue,
            "location": record.location,
            "comments": record.comments,
            "disposition": record.disposition,
            "ica": record.ica,
            "rca": record.rca,
            "pca": record.pca,
            "comments2": record.comments2,
            "status": record.status,
            "source_file": record.source_file,
            "is_valid": record.is_valid,
        }