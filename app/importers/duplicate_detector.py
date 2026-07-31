"""
app/importers/duplicate_detector.py

MotorTracker
Detecta registros duplicados entre el reporte
y la base de datos existente.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Iterable

from app.models.motor_record import MotorRecord
from app.utils.logger import LoggerManager


@dataclass(slots=True)
class DuplicateResult:
    """
    Resultado del análisis de un registro.
    """

    record: MotorRecord
    is_duplicate: bool
    reason: str = ""
    matched_record: MotorRecord | None = None


class DuplicateDetector:
    """
    Detecta duplicados mediante NCT, VIN y trazabilidad.
    """

    def __init__(
        self,
        existing_records: Iterable[MotorRecord] | None = None,
    ) -> None:
        self.existing_records: list[MotorRecord] = list(
            existing_records or []
        )

        self.nct_index: dict[str, MotorRecord] = {}
        self.vin_index: dict[str, MotorRecord] = {}
        self.traceability_index: dict[str, MotorRecord] = {}
        self.combined_index: dict[
            tuple[str, str],
            MotorRecord
        ] = {}

        self._build_indexes()

    # =========================================================
    # PUBLIC
    # =========================================================

    def set_existing_records(
        self,
        records: Iterable[MotorRecord],
    ) -> None:
        """
        Reemplaza los registros existentes y reconstruye índices.
        """

        self.existing_records = list(records)
        self._build_indexes()

    def analyze(
        self,
        records: Iterable[MotorRecord],
    ) -> list[DuplicateResult]:
        """
        Analiza una colección de registros.
        """

        results: list[DuplicateResult] = []
        current_batch_keys: set[tuple[str, str, str]] = set()

        for record in records:
            result = self.check_record(
                record=record,
                current_batch_keys=current_batch_keys,
            )

            results.append(result)

            if not result.is_duplicate:
                current_batch_keys.add(
                    self._batch_key(record)
                )

        duplicate_count = sum(
            1
            for result in results
            if result.is_duplicate
        )

        LoggerManager.info(
            f"Duplicados detectados: {duplicate_count}"
        )

        return results

    def check_record(
        self,
        record: MotorRecord,
        current_batch_keys: set[
            tuple[str, str, str]
        ] | None = None,
    ) -> DuplicateResult:
        """
        Comprueba si un registro ya existe.
        """

        if not record.is_valid:
            return DuplicateResult(
                record=record,
                is_duplicate=True,
                reason="Registro inválido: no contiene NCT ni VIN.",
            )

        normalized_nct = self.normalize(record.nct)
        normalized_vin = self.normalize(record.vin)
        normalized_traceability = self.normalize(
            record.traceability
        )

        combined_key = (
            normalized_nct,
            normalized_vin,
        )

        if (
            normalized_nct
            and normalized_vin
            and combined_key in self.combined_index
        ):
            matched = self.combined_index[combined_key]

            return DuplicateResult(
                record=record,
                is_duplicate=True,
                reason="Coincidencia exacta por NCT + VIN.",
                matched_record=matched,
            )

        if (
            normalized_nct
            and normalized_nct in self.nct_index
        ):
            matched = self.nct_index[normalized_nct]

            return DuplicateResult(
                record=record,
                is_duplicate=True,
                reason="El NCT ya existe en la base.",
                matched_record=matched,
            )

        if (
            normalized_vin
            and normalized_vin in self.vin_index
        ):
            matched = self.vin_index[normalized_vin]

            return DuplicateResult(
                record=record,
                is_duplicate=True,
                reason="El VIN ya existe en la base.",
                matched_record=matched,
            )

        if (
            normalized_traceability
            and normalized_traceability
            in self.traceability_index
        ):
            matched = self.traceability_index[
                normalized_traceability
            ]

            return DuplicateResult(
                record=record,
                is_duplicate=True,
                reason="La trazabilidad ya existe en la base.",
                matched_record=matched,
            )

        if current_batch_keys is not None:
            batch_key = self._batch_key(record)

            if batch_key in current_batch_keys:
                return DuplicateResult(
                    record=record,
                    is_duplicate=True,
                    reason=(
                        "Registro repetido dentro del mismo reporte."
                    ),
                )

        return DuplicateResult(
            record=record,
            is_duplicate=False,
        )

    def get_new_records(
        self,
        records: Iterable[MotorRecord],
    ) -> list[MotorRecord]:
        """
        Devuelve solamente los registros no duplicados.
        """

        return [
            result.record
            for result in self.analyze(records)
            if not result.is_duplicate
        ]

    def get_duplicate_records(
        self,
        records: Iterable[MotorRecord],
    ) -> list[MotorRecord]:
        """
        Devuelve solamente los registros duplicados.
        """

        return [
            result.record
            for result in self.analyze(records)
            if result.is_duplicate
        ]

    def count_duplicates(
        self,
        records: Iterable[MotorRecord],
    ) -> int:
        """
        Cuenta los registros duplicados.
        """

        return sum(
            1
            for result in self.analyze(records)
            if result.is_duplicate
        )

    def summary(
        self,
        records: Iterable[MotorRecord],
    ) -> dict[str, int]:
        """
        Genera un resumen del análisis.
        """

        results = self.analyze(records)

        total = len(results)
        duplicates = sum(
            1
            for result in results
            if result.is_duplicate
        )
        new_records = total - duplicates

        reasons = Counter(
            result.reason
            for result in results
            if result.is_duplicate
        )

        return {
            "total": total,
            "new": new_records,
            "duplicates": duplicates,
            "invalid": reasons.get(
                "Registro inválido: no contiene NCT ni VIN.",
                0,
            ),
            "duplicate_nct": reasons.get(
                "El NCT ya existe en la base.",
                0,
            ),
            "duplicate_vin": reasons.get(
                "El VIN ya existe en la base.",
                0,
            ),
            "duplicate_traceability": reasons.get(
                "La trazabilidad ya existe en la base.",
                0,
            ),
            "duplicate_combined": reasons.get(
                "Coincidencia exacta por NCT + VIN.",
                0,
            ),
            "duplicate_batch": reasons.get(
                "Registro repetido dentro del mismo reporte.",
                0,
            ),
        }

    # =========================================================
    # INDEXES
    # =========================================================

    def _build_indexes(self) -> None:
        """
        Construye índices para acelerar la detección.
        """

        self.nct_index.clear()
        self.vin_index.clear()
        self.traceability_index.clear()
        self.combined_index.clear()

        for record in self.existing_records:
            normalized_nct = self.normalize(record.nct)
            normalized_vin = self.normalize(record.vin)
            normalized_traceability = self.normalize(
                record.traceability
            )

            if normalized_nct:
                self.nct_index.setdefault(
                    normalized_nct,
                    record,
                )

            if normalized_vin:
                self.vin_index.setdefault(
                    normalized_vin,
                    record,
                )

            if normalized_traceability:
                self.traceability_index.setdefault(
                    normalized_traceability,
                    record,
                )

            if normalized_nct and normalized_vin:
                self.combined_index.setdefault(
                    (
                        normalized_nct,
                        normalized_vin,
                    ),
                    record,
                )

    # =========================================================
    # HELPERS
    # =========================================================

    @staticmethod
    def normalize(value: object) -> str:
        """
        Normaliza valores para realizar comparaciones.
        """

        if value is None:
            return ""

        text = str(value)
        text = text.replace("\xa0", " ")
        text = text.strip().upper()

        return "".join(text.split())

    def _batch_key(
        self,
        record: MotorRecord,
    ) -> tuple[str, str, str]:
        """
        Genera una clave para detectar duplicados internos.
        """

        return (
            self.normalize(record.nct),
            self.normalize(record.vin),
            self.normalize(record.traceability),
        )