"""
app/importers/report_reader.py

MotorTracker
Lee el reporte General Inquiry y lo convierte
en registros listos para importar.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from app.utils.logger import LoggerManager
from app.core.exceptions import ReportReadError


class ReportReader:

    def __init__(self) -> None:

        self.dataframe: pd.DataFrame | None = None

    # -------------------------------------------------------
    # PUBLIC
    # -------------------------------------------------------

    def read(self, file: Path) -> pd.DataFrame:

        LoggerManager.info(f"Leyendo reporte: {file.name}")

        try:

            self.dataframe = pd.read_excel(
                file,
                engine="openpyxl",
                dtype=str
            )

            self.__normalize()

            LoggerManager.info(
                f"Registros encontrados: {len(self.dataframe)}"
            )

            return self.dataframe

        except Exception as e:

            LoggerManager.exception(
                "No fue posible leer el reporte."
            )

            raise ReportReadError(str(e))

    # -------------------------------------------------------
    # PRIVATE
    # -------------------------------------------------------

    def __normalize(self):

        if self.dataframe is None:
            return

        # Eliminar espacios de encabezados
        self.dataframe.columns = (
            self.dataframe.columns
            .astype(str)
            .str.strip()
        )

        # Convertir NaN a vacío
        self.dataframe.fillna(
            "",
            inplace=True
        )

        # Eliminar espacios
        self.dataframe = self.dataframe.apply(
            lambda column: column.astype(str).str.strip()
        )

        # Eliminar filas completamente vacías
        self.dataframe.dropna(
            how="all",
            inplace=True
        )

        self.dataframe.reset_index(
            drop=True,
            inplace=True
        )

    # -------------------------------------------------------

    def columns(self) -> list[str]:

        if self.dataframe is None:
            return []

        return list(self.dataframe.columns)

    # -------------------------------------------------------

    def rows(self) -> int:

        if self.dataframe is None:
            return 0

        return len(self.dataframe)

    # -------------------------------------------------------

    def preview(
        self,
        rows: int = 10
    ) -> pd.DataFrame:

        if self.dataframe is None:
            raise ReportReadError(
                "El reporte no ha sido cargado."
            )

        return self.dataframe.head(rows)

    # -------------------------------------------------------

    def records(self) -> list[dict[str, Any]]:

        if self.dataframe is None:
            return []

        return self.dataframe.to_dict(
            orient="records"
        )

    # -------------------------------------------------------

    def get_column(
        self,
        column: str
    ) -> list[Any]:

        if self.dataframe is None:
            return []

        if column not in self.dataframe.columns:
            return []

        return self.dataframe[column].tolist()

    # -------------------------------------------------------

    def exists_column(
        self,
        column: str
    ) -> bool:

        if self.dataframe is None:
            return False

        return column in self.dataframe.columns