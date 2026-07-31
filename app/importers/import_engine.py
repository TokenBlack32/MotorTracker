"""
app/importers/import_engine.py

MotorTracker
Coordina el proceso completo de importación:

Reporte Excel
    ↓
ReportReader
    ↓
MotorRecord
    ↓
DatabaseReader
    ↓
DuplicateDetector
    ↓
DatabaseWriter
    ↓
Mover reporte a Processed
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Iterable

from app.core.exceptions import (
    DatabaseReadError,
    DatabaseWriteError,
    ImportCancelledError,
    ImportErrorMT,
    ReportReadError,
)
from app.importers.database_reader import DatabaseReader
from app.importers.database_writer import DatabaseWriter
from app.importers.duplicate_detector import (
    DuplicateDetector,
    DuplicateResult,
)
from app.importers.report_reader import ReportReader
from app.models.motor_record import MotorRecord
from app.utils.file_manager import FileManager
from app.utils.logger import ImportLogger, LoggerManager


@dataclass(slots=True)
class ImportProgress:
    """
    Representa el progreso actual de una importación.
    """

    stage: str
    message: str
    current: int = 0
    total: int = 0

    @property
    def percentage(self) -> int:
        """
        Devuelve el porcentaje de progreso.
        """

        if self.total <= 0:
            return 0

        percentage = round(
            (self.current / self.total) * 100
        )

        return min(
            max(percentage, 0),
            100,
        )


@dataclass(slots=True)
class ImportResult:
    """
    Resultado completo del proceso de importación.
    """

    success: bool = False
    cancelled: bool = False

    report_path: str = ""
    processed_path: str = ""
    database_path: str = ""
    backup_path: str = ""

    total_records: int = 0
    valid_records: int = 0
    invalid_records: int = 0
    new_records: int = 0
    duplicate_records: int = 0
    imported_records: int = 0
    error_records: int = 0

    inserted_rows: list[int] = field(
        default_factory=list
    )

    duplicates: list[DuplicateResult] = field(
        default_factory=list
    )

    errors: list[str] = field(
        default_factory=list
    )

    started_at: datetime = field(
        default_factory=datetime.now
    )

    finished_at: datetime | None = None

    @property
    def duration_seconds(self) -> float:
        """
        Devuelve la duración total de la importación.
        """

        end_time = self.finished_at or datetime.now()

        return round(
            (
                end_time - self.started_at
            ).total_seconds(),
            2,
        )

    def finish(self) -> None:
        """
        Marca el resultado como finalizado.
        """

        self.finished_at = datetime.now()

    def to_dict(self) -> dict[str, Any]:
        """
        Convierte el resultado a un diccionario.
        """

        return {
            "success": self.success,
            "cancelled": self.cancelled,
            "report_path": self.report_path,
            "processed_path": self.processed_path,
            "database_path": self.database_path,
            "backup_path": self.backup_path,
            "total_records": self.total_records,
            "valid_records": self.valid_records,
            "invalid_records": self.invalid_records,
            "new_records": self.new_records,
            "duplicate_records": self.duplicate_records,
            "imported_records": self.imported_records,
            "error_records": self.error_records,
            "inserted_rows": list(self.inserted_rows),
            "errors": list(self.errors),
            "started_at": self.started_at.isoformat(),
            "finished_at": (
                self.finished_at.isoformat()
                if self.finished_at
                else None
            ),
            "duration_seconds": self.duration_seconds,
        }


ProgressCallback = Callable[[ImportProgress], None]


class ImportEngine:
    """
    Coordina todos los servicios involucrados en la importación.
    """

    def __init__(
        self,
        file_manager: FileManager | None = None,
        progress_callback: ProgressCallback | None = None,
    ) -> None:
        self.file_manager = file_manager or FileManager()
        self.progress_callback = progress_callback

        self.report_reader = ReportReader()
        self.database_reader = DatabaseReader()

        self._cancel_requested = False
        self._running = False

    # =========================================================
    # PUBLIC
    # =========================================================

    @property
    def is_running(self) -> bool:
        """
        Indica si existe una importación en ejecución.
        """

        return self._running

    def cancel(self) -> None:
        """
        Solicita la cancelación de la importación activa.
        """

        if self._running:
            self._cancel_requested = True

            LoggerManager.warning(
                "Se solicitó cancelar la importación."
            )

    def import_latest_report(
        self,
        move_to_processed: bool = True,
        create_backup: bool = True,
    ) -> ImportResult:
        """
        Importa el reporte más reciente de la carpeta Reports.
        """

        report_path = self.file_manager.get_latest_report()

        return self.import_report(
            report_path=report_path,
            move_to_processed=move_to_processed,
            create_backup=create_backup,
        )

    def import_report(
        self,
        report_path: Path | str,
        move_to_processed: bool = True,
        create_backup: bool = True,
    ) -> ImportResult:
        """
        Ejecuta el proceso completo de importación.

        Args:
            report_path:
                Ruta del reporte que será procesado.

            move_to_processed:
                Mueve el reporte a Processed cuando la importación
                termina correctamente.

            create_backup:
                Crea una copia de seguridad de la base antes de
                insertar registros.

        Returns:
            ImportResult con el resumen completo del proceso.
        """

        if self._running:
            raise ImportErrorMT(
                "Ya existe una importación en ejecución."
            )

        self._running = True
        self._cancel_requested = False

        report = Path(report_path)

        result = ImportResult(
            report_path=str(report)
        )

        import_logger = ImportLogger()

        try:
            self._notify(
                stage="initializing",
                message="Preparando la importación.",
            )

            self._check_cancelled()

            self.file_manager.create_folders()
            self.file_manager.validate_excel(report)

            database_path = self.file_manager.get_database_path()

            result.database_path = str(database_path)

            import_logger.start(report.name)

            # -------------------------------------------------
            # 1. LEER REPORTE
            # -------------------------------------------------

            self._notify(
                stage="reading_report",
                message=f"Leyendo reporte {report.name}.",
            )

            report_dataframe = self.report_reader.read(report)

            raw_rows = report_dataframe.to_dict(
                orient="records"
            )

            result.total_records = len(raw_rows)

            self._check_cancelled()

            # -------------------------------------------------
            # 2. CONVERTIR A MOTOR RECORDS
            # -------------------------------------------------

            self._notify(
                stage="mapping_records",
                message="Convirtiendo filas del reporte.",
                current=0,
                total=result.total_records,
            )

            report_records = self._build_motor_records(
                rows=raw_rows,
                source_file=report.name,
                result=result,
            )

            valid_records = [
                record
                for record in report_records
                if record.is_valid
            ]

            invalid_records = [
                record
                for record in report_records
                if not record.is_valid
            ]

            result.valid_records = len(valid_records)
            result.invalid_records = len(invalid_records)

            self._check_cancelled()

            # -------------------------------------------------
            # 3. LEER BASE
            # -------------------------------------------------

            self._notify(
                stage="reading_database",
                message="Leyendo registros existentes.",
            )

            existing_records = self.database_reader.read(
                database_path
            )

            self._check_cancelled()

            # -------------------------------------------------
            # 4. DETECTAR DUPLICADOS
            # -------------------------------------------------

            self._notify(
                stage="detecting_duplicates",
                message="Detectando registros duplicados.",
                current=0,
                total=len(valid_records),
            )

            duplicate_detector = DuplicateDetector(
                existing_records=existing_records
            )

            duplicate_results = duplicate_detector.analyze(
                valid_records
            )

            new_records: list[MotorRecord] = []
            duplicates: list[DuplicateResult] = []

            for index, duplicate_result in enumerate(
                duplicate_results,
                start=1,
            ):
                self._check_cancelled()

                if duplicate_result.is_duplicate:
                    duplicate_result.record.status = "DUPLICATE"
                    duplicates.append(duplicate_result)
                else:
                    duplicate_result.record.status = "READY"
                    new_records.append(
                        duplicate_result.record
                    )

                self._notify(
                    stage="detecting_duplicates",
                    message="Analizando duplicados.",
                    current=index,
                    total=len(valid_records),
                )

            result.new_records = len(new_records)
            result.duplicate_records = len(duplicates)
            result.duplicates = duplicates

            self._check_cancelled()

            # -------------------------------------------------
            # 5. ESCRIBIR NUEVOS REGISTROS
            # -------------------------------------------------

            if new_records:
                self._notify(
                    stage="writing_database",
                    message=(
                        f"Insertando {len(new_records)} "
                        "registros nuevos."
                    ),
                    current=0,
                    total=len(new_records),
                )

                writer = DatabaseWriter(
                    database_path=database_path,
                    sheet_name=self.database_reader.sheet_name,
                    backup_folder=self.file_manager.backup_folder,
                )

                inserted_rows = writer.write(
                    records=new_records,
                    create_backup=create_backup,
                )

                result.inserted_rows = inserted_rows
                result.imported_records = len(inserted_rows)

                for record in new_records:
                    record.status = "IMPORTED"

                self._notify(
                    stage="writing_database",
                    message="Registros insertados correctamente.",
                    current=len(inserted_rows),
                    total=len(new_records),
                )

            else:
                LoggerManager.info(
                    "El reporte no contiene registros nuevos."
                )

                self._notify(
                    stage="writing_database",
                    message="No se encontraron registros nuevos.",
                )

            self._check_cancelled()

            # -------------------------------------------------
            # 6. MOVER REPORTE PROCESADO
            # -------------------------------------------------

            if move_to_processed:
                self._notify(
                    stage="moving_report",
                    message="Moviendo reporte a Processed.",
                )

                processed_path = (
                    self.file_manager.move_to_processed(report)
                )

                result.processed_path = str(processed_path)

            # -------------------------------------------------
            # 7. FINALIZAR
            # -------------------------------------------------

            result.success = True
            result.finish()

            self._notify(
                stage="completed",
                message="Importación completada.",
                current=100,
                total=100,
            )

            import_logger.finish(
                imported=result.imported_records,
                duplicates=result.duplicate_records,
                errors=result.error_records,
            )

            LoggerManager.info(
                "Resumen de importación: "
                f"total={result.total_records}, "
                f"nuevos={result.new_records}, "
                f"duplicados={result.duplicate_records}, "
                f"importados={result.imported_records}"
            )

            return result

        except ImportCancelledError as error:
            result.cancelled = True
            result.success = False
            result.errors.append(str(error))
            result.finish()

            LoggerManager.warning(
                "La importación fue cancelada."
            )

            self._notify(
                stage="cancelled",
                message="Importación cancelada.",
            )

            return result

        except (
            ReportReadError,
            DatabaseReadError,
            DatabaseWriteError,
        ) as error:
            result.success = False
            result.error_records += 1
            result.errors.append(str(error))
            result.finish()

            LoggerManager.exception(
                "La importación no pudo completarse."
            )

            self._notify(
                stage="error",
                message=str(error),
            )

            return result

        except Exception as error:
            result.success = False
            result.error_records += 1
            result.errors.append(str(error))
            result.finish()

            LoggerManager.exception(
                "Error inesperado durante la importación."
            )

            self._notify(
                stage="error",
                message=(
                    "Ocurrió un error inesperado durante "
                    "la importación."
                ),
            )

            return result

        finally:
            self._running = False
            self._cancel_requested = False

    def preview_report(
        self,
        report_path: Path | str,
    ) -> list[MotorRecord]:
        """
        Lee y convierte un reporte sin modificar la base.
        """

        report = Path(report_path)

        self.file_manager.validate_excel(report)

        dataframe = self.report_reader.read(report)

        rows = dataframe.to_dict(
            orient="records"
        )

        preview_result = ImportResult(
            report_path=str(report),
            total_records=len(rows),
        )

        return self._build_motor_records(
            rows=rows,
            source_file=report.name,
            result=preview_result,
        )

    def analyze_report(
        self,
        report_path: Path | str,
    ) -> ImportResult:
        """
        Lee el reporte y detecta duplicados sin escribir ni mover
        ningún archivo.
        """

        report = Path(report_path)

        result = ImportResult(
            report_path=str(report)
        )

        try:
            self.file_manager.validate_excel(report)

            database_path = self.file_manager.get_database_path()

            result.database_path = str(database_path)

            dataframe = self.report_reader.read(report)

            rows = dataframe.to_dict(
                orient="records"
            )

            result.total_records = len(rows)

            records = self._build_motor_records(
                rows=rows,
                source_file=report.name,
                result=result,
            )

            valid_records = [
                record
                for record in records
                if record.is_valid
            ]

            result.valid_records = len(valid_records)
            result.invalid_records = (
                len(records) - len(valid_records)
            )

            existing_records = self.database_reader.read(
                database_path
            )

            detector = DuplicateDetector(
                existing_records
            )

            analysis = detector.analyze(
                valid_records
            )

            result.duplicates = [
                item
                for item in analysis
                if item.is_duplicate
            ]

            result.duplicate_records = len(
                result.duplicates
            )

            result.new_records = sum(
                1
                for item in analysis
                if not item.is_duplicate
            )

            result.success = True
            result.finish()

            return result

        except Exception as error:
            result.success = False
            result.errors.append(str(error))
            result.finish()

            LoggerManager.exception(
                "No fue posible analizar el reporte."
            )

            return result

    # =========================================================
    # RECORD MAPPING
    # =========================================================

    def _build_motor_records(
        self,
        rows: Iterable[dict[str, Any]],
        source_file: str,
        result: ImportResult,
    ) -> list[MotorRecord]:
        """
        Convierte las filas leídas en objetos MotorRecord.
        """

        rows_list = list(rows)
        records: list[MotorRecord] = []

        for index, row in enumerate(
            rows_list,
            start=1,
        ):
            self._check_cancelled()

            try:
                cleaned_row = self._clean_report_row(row)

                record = MotorRecord.from_report_row(
                    cleaned_row
                )

                record.source_file = source_file
                record.status = (
                    "NEW"
                    if record.is_valid
                    else "INVALID"
                )

                records.append(record)

            except Exception as error:
                result.error_records += 1
                result.errors.append(
                    f"Fila {index}: {error}"
                )

                LoggerManager.warning(
                    f"No se pudo convertir la fila {index}: "
                    f"{error}"
                )

            self._notify(
                stage="mapping_records",
                message="Convirtiendo registros.",
                current=index,
                total=len(rows_list),
            )

        return records

    @staticmethod
    def _clean_report_row(
        row: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Limpia los nombres de columnas y sus valores.
        """

        cleaned: dict[str, Any] = {}

        for key, value in row.items():
            normalized_key = str(key).strip()

            if value is None:
                cleaned[normalized_key] = ""
                continue

            if isinstance(value, str):
                value = value.replace("\x00", "")
                value = value.replace("\xa0", " ")
                value = value.strip()

            cleaned[normalized_key] = value

        return cleaned

    # =========================================================
    # CONTROL
    # =========================================================

    def _check_cancelled(self) -> None:
        """
        Interrumpe el proceso cuando se solicitó cancelación.
        """

        if self._cancel_requested:
            raise ImportCancelledError(
                "La importación fue cancelada por el usuario."
            )

    def _notify(
        self,
        stage: str,
        message: str,
        current: int = 0,
        total: int = 0,
    ) -> None:
        """
        Envía información de progreso a la interfaz.
        """

        progress = ImportProgress(
            stage=stage,
            message=message,
            current=current,
            total=total,
        )

        LoggerManager.debug(
            f"[{stage}] {message} "
            f"({progress.percentage}%)"
        )

        if self.progress_callback is None:
            return

        try:
            self.progress_callback(progress)

        except Exception:
            LoggerManager.exception(
                "El callback de progreso produjo un error."
            )