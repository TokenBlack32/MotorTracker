"""
app/importers/database_reader.py

MotorTracker
Lee los registros existentes de MASTER TRACK MOTORES.xlsx.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

from openpyxl import load_workbook
from openpyxl.worksheet.worksheet import Worksheet

from app.core.exceptions import (
    DatabaseNotFoundError,
    DatabaseReadError,
    MissingColumnError,
)
from app.models.motor_record import MotorRecord
from app.utils.logger import LoggerManager


class DatabaseReader:
    """
    Lee la hoja principal de la base de motores y convierte
    cada fila existente en una instancia de MotorRecord.
    """

    REQUIRED_COLUMNS = {
        "MODEL",
        "PN",
        "SUPPLIER",
        "TRACEABILITY",
        "NO. MOTORS",
        "VIN",
        "NCT",
        "SDA/ RMA",
        "DTC",
        "ISSUE",
        "LOCATION",
        "COMMENTS",
        "DISPOSITION",
        "ICA",
        "RCA",
        "PCA",
        "COMMENTS2",
    }

    HEADER_ALIASES = {
        "MODEL": "MODEL",
        "PN": "PN",
        "PART NUMBER": "PN",
        "SUPPLIER": "SUPPLIER",
        "TRACEABILITY": "TRACEABILITY",
        "TRACEBILITY": "TRACEABILITY",
        "NO. MOTORS": "NO. MOTORS",
        "NO MOTORS": "NO. MOTORS",
        "NUMBER OF MOTORS": "NO. MOTORS",
        "VIN": "VIN",
        "NCT": "NCT",
        "N/C": "NCT",
        "N/C #": "NCT",
        "SDA/RMA": "SDA/ RMA",
        "SDA / RMA": "SDA/ RMA",
        "SDA/ RMA": "SDA/ RMA",
        "SDA RMA": "SDA/ RMA",
        "DTC": "DTC",
        "ISSUE": "ISSUE",
        "LOCATION": "LOCATION",
        "COMMENTS": "COMMENTS",
        "DISPOSITION": "DISPOSITION",
        "ICA": "ICA",
        "RCA": "RCA",
        "PCA": "PCA",
        "COMMENTS2": "COMMENTS2",
        "COMMENTS 2": "COMMENTS2",
    }

    PREFERRED_SHEET_NAMES = (
        "Engines DEP KEP",
        "Engines",
        "Motor Tracker",
        "Master Track",
    )

    def __init__(self) -> None:
        self.database_path: Path | None = None
        self.sheet_name: str = ""
        self.header_row: int = 0
        self.column_map: dict[str, int] = {}
        self.records: list[MotorRecord] = []

    # =========================================================
    # PUBLIC
    # =========================================================

    def read(self, database_path: Path | str) -> list[MotorRecord]:
        """
        Abre la base de datos y obtiene todos los registros válidos.
        """

        path = Path(database_path)

        if not path.exists():
            raise DatabaseNotFoundError(
                f"No se encontró la base de datos: {path}"
            )

        if path.suffix.lower() not in {".xlsx", ".xlsm"}:
            raise DatabaseReadError(
                "La base debe tener extensión .xlsx o .xlsm."
            )

        LoggerManager.info(
            f"Leyendo base de datos: {path.name}"
        )

        try:
            workbook = load_workbook(
                filename=path,
                read_only=True,
                data_only=True,
                keep_links=True,
            )

            worksheet = self._find_database_sheet(workbook.worksheets)

            self.database_path = path
            self.sheet_name = worksheet.title
            self.header_row = self._find_header_row(worksheet)
            self.column_map = self._build_column_map(
                worksheet,
                self.header_row,
            )

            self._validate_required_columns()

            self.records = self._read_records(
                worksheet=worksheet,
                header_row=self.header_row,
            )

            workbook.close()

            LoggerManager.info(
                f"Hoja de base detectada: {self.sheet_name}"
            )
            LoggerManager.info(
                f"Fila de encabezados detectada: {self.header_row}"
            )
            LoggerManager.info(
                f"Registros existentes: {len(self.records)}"
            )

            return self.records

        except (
            DatabaseNotFoundError,
            DatabaseReadError,
            MissingColumnError,
        ):
            raise

        except PermissionError as error:
            raise DatabaseReadError(
                "No se pudo abrir la base. "
                "Verifica que el archivo no esté abierto en Excel."
            ) from error

        except Exception as error:
            LoggerManager.exception(
                "Error leyendo la base de datos."
            )

            raise DatabaseReadError(
                f"No fue posible leer la base: {error}"
            ) from error

    def get_records(self) -> list[MotorRecord]:
        """
        Devuelve una copia de los registros cargados.
        """

        return list(self.records)

    def get_duplicate_keys(self) -> set[tuple[str, str]]:
        """
        Devuelve las claves NCT + VIN existentes.
        """

        return {
            record.duplicate_key
            for record in self.records
            if record.is_valid
        }

    def get_nct_values(self) -> set[str]:
        """
        Devuelve los valores NCT existentes normalizados.
        """

        return {
            self._normalize_key(record.nct)
            for record in self.records
            if self._normalize_key(record.nct)
        }

    def get_vin_values(self) -> set[str]:
        """
        Devuelve los valores VIN existentes normalizados.
        """

        return {
            self._normalize_key(record.vin)
            for record in self.records
            if self._normalize_key(record.vin)
        }

    def get_traceability_values(self) -> set[str]:
        """
        Devuelve las trazabilidades existentes normalizadas.
        """

        return {
            self._normalize_key(record.traceability)
            for record in self.records
            if self._normalize_key(record.traceability)
        }

    def get_last_data_row(self) -> int:
        """
        Calcula la siguiente fila disponible de la hoja principal.
        """

        if not self.database_path:
            raise DatabaseReadError(
                "La base de datos todavía no ha sido cargada."
            )

        workbook = load_workbook(
            filename=self.database_path,
            read_only=True,
            data_only=True,
        )

        worksheet = workbook[self.sheet_name]

        last_row = self.header_row

        for row_number in range(
            worksheet.max_row,
            self.header_row,
            -1,
        ):
            if self._row_has_data(
                worksheet,
                row_number,
            ):
                last_row = row_number
                break

        workbook.close()

        return last_row

    def next_available_row(self) -> int:
        """
        Devuelve la fila donde debe insertarse el siguiente registro.
        """

        return self.get_last_data_row() + 1

    def summary(self) -> dict[str, Any]:
        """
        Devuelve información de la base cargada.
        """

        return {
            "database_path": (
                str(self.database_path)
                if self.database_path
                else ""
            ),
            "sheet_name": self.sheet_name,
            "header_row": self.header_row,
            "records": len(self.records),
            "columns": dict(self.column_map),
            "next_available_row": (
                self.next_available_row()
                if self.database_path
                else None
            ),
        }

    # =========================================================
    # SHEET DETECTION
    # =========================================================

    def _find_database_sheet(
        self,
        worksheets: Iterable[Worksheet],
    ) -> Worksheet:
        """
        Busca primero nombres conocidos y después una hoja
        que contenga los encabezados principales.
        """

        worksheet_list = list(worksheets)

        for preferred_name in self.PREFERRED_SHEET_NAMES:
            for worksheet in worksheet_list:
                if (
                    worksheet.title.strip().casefold()
                    == preferred_name.casefold()
                ):
                    try:
                        self._find_header_row(worksheet)
                        return worksheet
                    except MissingColumnError:
                        continue

        best_sheet: Worksheet | None = None
        best_score = 0

        for worksheet in worksheet_list:
            score = self._calculate_sheet_score(worksheet)

            if score > best_score:
                best_sheet = worksheet
                best_score = score

        if best_sheet is None or best_score < 5:
            raise DatabaseReadError(
                "No se encontró una hoja con la estructura "
                "de MASTER TRACK MOTORES."
            )

        return best_sheet

    def _calculate_sheet_score(
        self,
        worksheet: Worksheet,
    ) -> int:
        """
        Calcula cuántos encabezados conocidos contiene una hoja.
        """

        highest_score = 0
        rows_to_scan = min(worksheet.max_row, 20)

        for row_number in range(1, rows_to_scan + 1):
            score = 0

            for cell in worksheet[row_number]:
                normalized = self._normalize_header(cell.value)

                if normalized in self.HEADER_ALIASES:
                    score += 1

            highest_score = max(highest_score, score)

        return highest_score

    def _find_header_row(
        self,
        worksheet: Worksheet,
    ) -> int:
        """
        Detecta la fila que contiene los encabezados de la base.
        """

        rows_to_scan = min(worksheet.max_row, 30)
        best_row = 0
        best_score = 0

        for row_number in range(1, rows_to_scan + 1):
            detected_headers: set[str] = set()

            for cell in worksheet[row_number]:
                normalized = self._normalize_header(cell.value)
                canonical = self.HEADER_ALIASES.get(normalized)

                if canonical:
                    detected_headers.add(canonical)

            score = len(detected_headers)

            if score > best_score:
                best_score = score
                best_row = row_number

        if best_row == 0 or best_score < 5:
            raise MissingColumnError(
                f"No se encontró la fila de encabezados "
                f"en la hoja '{worksheet.title}'."
            )

        return best_row

    # =========================================================
    # COLUMN MAPPING
    # =========================================================

    def _build_column_map(
        self,
        worksheet: Worksheet,
        header_row: int,
    ) -> dict[str, int]:
        """
        Relaciona los nombres de columnas con su número en Excel.
        """

        column_map: dict[str, int] = {}

        for cell in worksheet[header_row]:
            normalized = self._normalize_header(cell.value)
            canonical = self.HEADER_ALIASES.get(normalized)

            if canonical and canonical not in column_map:
                column_map[canonical] = cell.column

        return column_map

    def _validate_required_columns(self) -> None:
        """
        Valida que la hoja tenga las columnas necesarias.
        """

        essential_columns = {
            "MODEL",
            "PN",
            "SUPPLIER",
            "TRACEABILITY",
            "NO. MOTORS",
            "VIN",
            "NCT",
            "ISSUE",
        }

        missing_columns = sorted(
            essential_columns - set(self.column_map)
        )

        if missing_columns:
            raise MissingColumnError(
                "Faltan columnas obligatorias en la base: "
                + ", ".join(missing_columns)
            )

    # =========================================================
    # RECORD READING
    # =========================================================

    def _read_records(
        self,
        worksheet: Worksheet,
        header_row: int,
    ) -> list[MotorRecord]:
        """
        Convierte las filas de Excel en MotorRecord.
        """

        records: list[MotorRecord] = []

        for row_number in range(
            header_row + 1,
            worksheet.max_row + 1,
        ):
            row_data = self._read_row(
                worksheet,
                row_number,
            )

            if self._is_empty_row(row_data):
                continue

            record = self._row_to_motor_record(row_data)

            if not record.is_valid:
                continue

            records.append(record)

        return records

    def _read_row(
        self,
        worksheet: Worksheet,
        row_number: int,
    ) -> dict[str, Any]:
        """
        Obtiene una fila utilizando el mapa de columnas.
        """

        row_data: dict[str, Any] = {}

        for column_name, column_number in self.column_map.items():
            value = worksheet.cell(
                row=row_number,
                column=column_number,
            ).value

            row_data[column_name] = self._clean_value(value)

        return row_data

    def _row_to_motor_record(
        self,
        row: dict[str, Any],
    ) -> MotorRecord:
        """
        Construye un MotorRecord desde una fila de la base.
        """

        sda_rma = self._as_text(
            row.get("SDA/ RMA")
        )

        return MotorRecord(
            model=self._as_text(
                row.get("MODEL")
            ),
            part_number=self._as_text(
                row.get("PN")
            ),
            supplier=self._as_text(
                row.get("SUPPLIER")
            ),
            traceability=self._as_text(
                row.get("TRACEABILITY")
            ),
            no_motors=self._as_integer(
                row.get("NO. MOTORS"),
                default=1,
            ),
            vin=self._as_text(
                row.get("VIN")
            ),
            nct=self._as_text(
                row.get("NCT")
            ),
            sda=sda_rma,
            rma=sda_rma,
            dtc=self._as_text(
                row.get("DTC")
            ),
            issue=self._as_text(
                row.get("ISSUE")
            ),
            location=self._as_text(
                row.get("LOCATION")
            ),
            comments=self._as_text(
                row.get("COMMENTS")
            ),
            disposition=self._as_text(
                row.get("DISPOSITION")
            ),
            ica=self._as_text(
                row.get("ICA")
            ),
            rca=self._as_text(
                row.get("RCA")
            ),
            pca=self._as_text(
                row.get("PCA")
            ),
            comments2=self._as_text(
                row.get("COMMENTS2")
            ),
            status="EXISTING",
            source_file=(
                self.database_path.name
                if self.database_path
                else ""
            ),
        )

    # =========================================================
    # HELPERS
    # =========================================================

    def _row_has_data(
        self,
        worksheet: Worksheet,
        row_number: int,
    ) -> bool:
        """
        Comprueba si una fila contiene información relevante.
        """

        important_columns = (
            "NCT",
            "VIN",
            "TRACEABILITY",
            "PN",
            "ISSUE",
        )

        for column_name in important_columns:
            column_number = self.column_map.get(column_name)

            if not column_number:
                continue

            value = worksheet.cell(
                row=row_number,
                column=column_number,
            ).value

            if self._as_text(value):
                return True

        return False

    @staticmethod
    def _is_empty_row(
        row: dict[str, Any],
    ) -> bool:
        """
        Comprueba si todos los valores de una fila están vacíos.
        """

        return not any(
            DatabaseReader._as_text(value)
            for value in row.values()
        )

    @staticmethod
    def _normalize_header(value: Any) -> str:
        """
        Normaliza encabezados para realizar comparaciones.
        """

        if value is None:
            return ""

        text = str(value)
        text = text.replace("\n", " ")
        text = text.replace("\r", " ")
        text = text.replace("\xa0", " ")
        text = " ".join(text.split())

        return text.strip().upper()

    @staticmethod
    def _normalize_key(value: Any) -> str:
        """
        Normaliza valores usados para detectar duplicados.
        """

        text = DatabaseReader._as_text(value)

        return "".join(
            text.upper().split()
        )

    @staticmethod
    def _clean_value(value: Any) -> Any:
        """
        Limpia valores obtenidos desde Excel.
        """

        if value is None:
            return ""

        if isinstance(value, str):
            value = value.replace("\xa0", " ")
            value = value.replace("\r\n", "\n")
            value = value.replace("\r", "\n")

            return value.strip()

        return value

    @staticmethod
    def _as_text(value: Any) -> str:
        """
        Convierte un valor de Excel a texto limpio.
        """

        if value is None:
            return ""

        if isinstance(value, float) and value.is_integer():
            return str(int(value))

        text = str(value)
        text = text.replace("\xa0", " ")

        return text.strip()

    @staticmethod
    def _as_integer(
        value: Any,
        default: int = 0,
    ) -> int:
        """
        Convierte un valor de Excel a entero.
        """

        if value in (None, ""):
            return default

        try:
            return int(float(value))
        except (TypeError, ValueError):
            return default