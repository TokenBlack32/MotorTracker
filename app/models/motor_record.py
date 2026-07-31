"""
app/models/motor_record.py

MotorTracker
Modelo principal de un registro de motor.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class MotorRecord:
    """
    Representa un motor dentro del sistema.
    """

    # ============================
    # DATOS DEL REPORTE
    # ============================

    nct: str = ""

    vin: str = ""

    traceability: str = ""

    part_number: str = ""

    supplier: str = ""

    issue: str = ""

    comments: str = ""

    location: str = ""

    dtc: str = ""

    model: str = ""

    department: str = ""

    defect_code: str = ""

    defect_description: str = ""

    report_date: str = ""

    hours: float = 0.0

    # ============================
    # DATOS DE LA BASE
    # ============================

    no_motors: int = 1

    sda: str = ""

    rma: str = ""

    disposition: str = ""

    ica: str = ""

    rca: str = ""

    pca: str = ""

    comments2: str = ""

    # ============================
    # SISTEMA
    # ============================

    imported_at: datetime = field(
        default_factory=datetime.now
    )

    source_file: str = ""

    status: str = "NEW"

    # ===================================================

    @property
    def duplicate_key(self) -> tuple:

        return (
            self.nct.strip().upper(),
            self.vin.strip().upper()
        )

    # ===================================================

    @property
    def search_key(self) -> str:

        return (
            f"{self.nct}"
            f"{self.vin}"
            f"{self.part_number}"
            f"{self.supplier}"
        ).upper()

    # ===================================================

    @property
    def has_vin(self) -> bool:

        return self.vin != ""

    # ===================================================

    @property
    def has_nct(self) -> bool:

        return self.nct != ""

    # ===================================================

    @property
    def is_valid(self) -> bool:

        return (
            self.has_nct
            or self.has_vin
        )

    # ===================================================

    def update(self, **kwargs) -> None:

        for key, value in kwargs.items():

            if hasattr(self, key):
                setattr(self, key, value)

    # ===================================================

    def to_dict(self) -> dict[str, Any]:

        return {

            "MODEL": self.model,

            "PN": self.part_number,

            "Supplier": self.supplier,

            "TRACEABILITY": self.traceability,

            "NO. MOTORS": self.no_motors,

            "VIN": self.vin,

            "NCT": self.nct,

            "SDA": self.sda,

            "RMA": self.rma,

            "DTC": self.dtc,

            "ISSUE": self.issue,

            "Location": self.location,

            "Comments": self.comments,

            "Disposition": self.disposition,

            "ICA": self.ica,

            "RCA": self.rca,

            "PCA": self.pca,

            "Comments2": self.comments2

        }

    # ===================================================

    @classmethod
    def from_report_row(
        cls,
        row: dict[str, Any]
    ) -> "MotorRecord":

        return cls(

            nct=row.get("N/C #", ""),

            part_number=row.get("Part Number", ""),

            supplier=row.get("Supplier", ""),

            issue=row.get("Problem Description", ""),

            comments=row.get("Comments", ""),

            location=row.get("Department", ""),

            department=row.get("Department", ""),

            defect_code=row.get("Defect Code", ""),

            defect_description=row.get(
                "Defect Description",
                ""
            ),

            vin=row.get("VIN", ""),

            traceability=row.get(
                "Traceability",
                row.get("VIN", "")
            ),

            dtc=row.get("DTC", ""),

            report_date=row.get("Date", "")

        )

    # ===================================================

    def __hash__(self):

        return hash(
            self.duplicate_key
        )

    # ===================================================

    def __eq__(
        self,
        other
    ):

        if not isinstance(
            other,
            MotorRecord
        ):
            return False

        return (
            self.duplicate_key ==
            other.duplicate_key
        )

    # ===================================================

    def __str__(self):

        return (
            f"[{self.nct}] "
            f"{self.part_number} "
            f"{self.supplier}"
        )