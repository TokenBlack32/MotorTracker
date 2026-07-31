"""
app/ui/workers/import_worker.py

MotorTracker
Worker para ejecutar análisis e importaciones en segundo plano.

Las operaciones de lectura y escritura de Excel pueden tardar varios
segundos. Este worker permite ejecutarlas en un QThread para evitar
que la interfaz gráfica se congele.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from PySide6.QtCore import QObject, Signal, Slot

from app.importers.import_engine import ImportProgress, ImportResult
from app.services.import_service import ImportService
from app.utils.logger import LoggerManager


WorkerAction = Literal[
    "analyze_latest",
    "analyze_report",
    "import_latest",
    "import_report",
    "preview_latest",
    "preview_report",
]


class ImportWorker(QObject):
    """
    Ejecuta una operación de ImportService dentro de un QThread.

    Señales:

        started:
            La operación comenzó.

        progress:
            Emite porcentaje, etapa y mensaje.

        completed:
            La operación terminó correctamente.

        failed:
            La operación produjo una excepción.

        cancelled:
            La operación fue cancelada.

        finished:
            Siempre se emite al terminar, exista éxito o error.
    """

    started = Signal(str)

    progress = Signal(
        int,
        str,
        str,
        int,
        int,
    )

    completed = Signal(dict)
    failed = Signal(str, str)
    cancelled = Signal(dict)
    finished = Signal()

    def __init__(
        self,
        action: WorkerAction,
        report_path: Path | str | None = None,
        move_to_processed: bool = True,
        create_backup: bool | None = None,
        parent: QObject | None = None,
    ) -> None:
        """
        Inicializa el worker.

        Args:
            action:
                Operación que será ejecutada.

            report_path:
                Ruta del reporte cuando la operación requiere
                un archivo específico.

            move_to_processed:
                Indica si el reporte debe moverse a Processed
                después de una importación exitosa.

            create_backup:
                Controla la creación de una copia de seguridad.
                Cuando es None, se utiliza config.json.

            parent:
                Objeto padre de Qt.
        """

        super().__init__(parent)

        self.action = action

        self.report_path = (
            Path(report_path)
            if report_path is not None
            else None
        )

        self.move_to_processed = move_to_processed
        self.create_backup = create_backup

        self._service: ImportService | None = None
        self._cancel_requested = False
        self._running = False

    # =========================================================
    # PROPERTIES
    # =========================================================

    @property
    def is_running(self) -> bool:
        """
        Indica si el worker está ejecutando una operación.
        """

        return self._running

    @property
    def cancel_requested(self) -> bool:
        """
        Indica si el usuario solicitó una cancelación.
        """

        return self._cancel_requested

    # =========================================================
    # EXECUTION
    # =========================================================

    @Slot()
    def run(self) -> None:
        """
        Ejecuta la operación configurada.

        Este método debe conectarse a QThread.started.
        """

        if self._running:
            return

        self._running = True
        self._cancel_requested = False

        action_name = self._get_action_name()

        self.started.emit(action_name)

        LoggerManager.info(
            f"Worker iniciado: {self.action}"
        )

        try:
            self._service = ImportService(
                progress_callback=self._handle_progress
            )

            result = self._execute_action()

            if self._cancel_requested:
                cancellation_data = self._build_cancelled_data(
                    result
                )

                self.cancelled.emit(cancellation_data)

                LoggerManager.info(
                    f"Worker cancelado: {self.action}"
                )

                return

            if isinstance(result, ImportResult):
                result_data = self._import_result_to_dict(
                    result
                )

                if result.cancelled:
                    self.cancelled.emit(result_data)
                elif result.success:
                    self.completed.emit(result_data)
                else:
                    error_message = self._get_result_error_message(
                        result
                    )

                    self.failed.emit(
                        error_message,
                        "",
                    )

                return

            if isinstance(result, list):
                self.completed.emit(
                    {
                        "success": True,
                        "action": self.action,
                        "records": result,
                        "records_count": len(result),
                    }
                )

                return

            if isinstance(result, dict):
                result.setdefault("success", True)
                result.setdefault("action", self.action)

                self.completed.emit(result)

                return

            self.completed.emit(
                {
                    "success": True,
                    "action": self.action,
                    "result": result,
                }
            )

        except Exception as error:
            LoggerManager.exception(
                f"Error en el worker {self.action}."
            )

            self.failed.emit(
                str(error),
                error.__class__.__name__,
            )

        finally:
            self._running = False
            self._service = None

            self.finished.emit()

            LoggerManager.info(
                f"Worker finalizado: {self.action}"
            )

    # =========================================================
    # CANCELLATION
    # =========================================================

    @Slot()
    def cancel(self) -> None:
        """
        Solicita la cancelación de la operación.

        La cancelación depende de que ImportEngine revise su estado
        durante las etapas de procesamiento.
        """

        self._cancel_requested = True

        if self._service is not None:
            try:
                self._service.cancel_import()

            except Exception:
                LoggerManager.exception(
                    "No fue posible solicitar la cancelación."
                )

    # =========================================================
    # ACTIONS
    # =========================================================

    def _execute_action(self) -> Any:
        """
        Ejecuta la acción seleccionada.
        """

        if self._service is None:
            raise RuntimeError(
                "ImportService no fue inicializado."
            )

        if self.action == "analyze_latest":
            return self._service.analyze_latest_report()

        if self.action == "analyze_report":
            report_path = self._require_report_path()

            return self._service.analyze_report(
                report_path
            )

        if self.action == "import_latest":
            return self._service.import_latest_report(
                move_to_processed=self.move_to_processed,
                create_backup=self.create_backup,
            )

        if self.action == "import_report":
            report_path = self._require_report_path()

            return self._service.import_report(
                report_path=report_path,
                move_to_processed=self.move_to_processed,
                create_backup=self.create_backup,
            )

        if self.action == "preview_latest":
            records = (
                self._service.preview_latest_report()
            )

            return [
                self._record_to_dict(record)
                for record in records
            ]

        if self.action == "preview_report":
            report_path = self._require_report_path()

            return (
                self._service.preview_report_as_dicts(
                    report_path
                )
            )

        raise ValueError(
            f"Acción de worker no soportada: {self.action}"
        )

    # =========================================================
    # PROGRESS
    # =========================================================

    def _handle_progress(
        self,
        progress: ImportProgress,
    ) -> None:
        """
        Reenvía el progreso del ImportEngine hacia la GUI.
        """

        percentage = self._safe_int(
            getattr(progress, "percentage", 0)
        )

        current = self._safe_int(
            getattr(progress, "current", 0)
        )

        total = self._safe_int(
            getattr(progress, "total", 0)
        )

        stage = str(
            getattr(progress, "stage", "")
            or ""
        )

        message = str(
            getattr(progress, "message", "")
            or ""
        )

        percentage = max(
            0,
            min(100, percentage),
        )

        self.progress.emit(
            percentage,
            stage,
            message,
            current,
            total,
        )

    # =========================================================
    # RESULT CONVERSION
    # =========================================================

    def _import_result_to_dict(
        self,
        result: ImportResult,
    ) -> dict[str, Any]:
        """
        Convierte ImportResult en un diccionario serializable.
        """

        if hasattr(result, "to_dict"):
            result_data = result.to_dict()
        else:
            result_data = {
                key: value
                for key, value in vars(result).items()
                if not key.startswith("_")
            }

        result_data["action"] = self.action

        return result_data

    @staticmethod
    def _record_to_dict(
        record: Any,
    ) -> dict[str, Any]:
        """
        Convierte un registro de vista previa en diccionario.
        """

        if hasattr(record, "to_dict"):
            return record.to_dict()

        if isinstance(record, dict):
            return record

        return {
            key: value
            for key, value in vars(record).items()
            if not key.startswith("_")
        }

    def _build_cancelled_data(
        self,
        result: Any,
    ) -> dict[str, Any]:
        """
        Construye la respuesta de una operación cancelada.
        """

        if isinstance(result, ImportResult):
            data = self._import_result_to_dict(
                result
            )
        else:
            data = {
                "action": self.action,
            }

        data["success"] = False
        data["cancelled"] = True

        return data

    @staticmethod
    def _get_result_error_message(
        result: ImportResult,
    ) -> str:
        """
        Obtiene el mensaje principal de un resultado fallido.
        """

        errors = getattr(
            result,
            "errors",
            [],
        )

        if errors:
            return "\n".join(
                str(error)
                for error in errors
            )

        return "La operación no pudo completarse."

    # =========================================================
    # HELPERS
    # =========================================================

    def _require_report_path(self) -> Path:
        """
        Obtiene la ruta requerida para acciones específicas.
        """

        if self.report_path is None:
            raise ValueError(
                "La operación requiere la ruta de un reporte."
            )

        return self.report_path

    def _get_action_name(self) -> str:
        """
        Devuelve el nombre visible de la operación.
        """

        names = {
            "analyze_latest": "Analizando reporte",
            "analyze_report": "Analizando reporte",
            "import_latest": "Importando reporte",
            "import_report": "Importando reporte",
            "preview_latest": "Cargando vista previa",
            "preview_report": "Cargando vista previa",
        }

        return names.get(
            self.action,
            self.action,
        )

    @staticmethod
    def _safe_int(
        value: Any,
    ) -> int:
        """
        Convierte un valor a entero sin producir excepciones.
        """

        try:
            return int(value)

        except (TypeError, ValueError):
            return 0