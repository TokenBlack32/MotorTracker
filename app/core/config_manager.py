"""
app/core/config_manager.py

MotorTracker
Configuration Manager

Autor: TokenBlack
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class ConfigManager:
    """
    Administra toda la configuración del sistema.
    """

    DEFAULT_CONFIG = {
        "app_name": "MotorTracker",
        "version": "1.0.0",
        "database": {
            "folder": "Database",
            "file": "MASTER TRACK MOTORES.xlsx",
            "backup": True
        },
        "reports": {
            "folder": "Reports",
            "processed_folder": "Processed",
            "extensions": [
                ".xlsx",
                ".xls"
            ]
        },
        "logs": {
            "folder": "Logs",
            "level": "INFO"
        },
        "import": {
            "auto_process": False,
            "duplicate_keys": [
                "NCT",
                "VIN"
            ]
        },
        "ui": {
            "theme": "Light"
        }
    }

    def __init__(self, config_path: str = "config.json") -> None:

        self.config_path = Path(config_path)
        self.config: dict[str, Any] = {}

        if not self.config_path.exists():
            self.create_default()

        self.load()
        self.validate()
        self.create_folders()

    # -------------------------------------------------
    # CONFIG
    # -------------------------------------------------

    def create_default(self) -> None:

        self.config = self.DEFAULT_CONFIG.copy()

        with open(
            self.config_path,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                self.config,
                file,
                indent=4,
                ensure_ascii=False
            )

    def load(self) -> None:

        with open(
            self.config_path,
            "r",
            encoding="utf-8"
        ) as file:

            self.config = json.load(file)

    def save(self) -> None:

        with open(
            self.config_path,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                self.config,
                file,
                indent=4,
                ensure_ascii=False
            )

    def reload(self) -> None:

        self.load()

    # -------------------------------------------------
    # GET
    # -------------------------------------------------

    def get(
        self,
        path: str,
        default: Any = None
    ) -> Any:

        keys = path.split(".")

        value = self.config

        try:

            for key in keys:
                value = value[key]

            return value

        except Exception:
            return default

    # -------------------------------------------------
    # SET
    # -------------------------------------------------

    def set(
        self,
        path: str,
        value: Any
    ) -> None:

        keys = path.split(".")

        data = self.config

        for key in keys[:-1]:

            if key not in data:
                data[key] = {}

            data = data[key]

        data[keys[-1]] = value

    # -------------------------------------------------
    # VALIDATION
    # -------------------------------------------------

    def validate(self) -> None:

        if "database" not in self.config:
            self.config["database"] = self.DEFAULT_CONFIG["database"]

        if "reports" not in self.config:
            self.config["reports"] = self.DEFAULT_CONFIG["reports"]

        if "logs" not in self.config:
            self.config["logs"] = self.DEFAULT_CONFIG["logs"]

        if "import" not in self.config:
            self.config["import"] = self.DEFAULT_CONFIG["import"]

        if "ui" not in self.config:
            self.config["ui"] = self.DEFAULT_CONFIG["ui"]

        self.save()

    # -------------------------------------------------
    # FOLDERS
    # -------------------------------------------------

    def create_folders(self) -> None:

        folders = [

            self.get("database.folder"),

            self.get("reports.folder"),

            self.get("reports.processed_folder"),

            self.get("logs.folder")

        ]

        for folder in folders:

            Path(folder).mkdir(
                parents=True,
                exist_ok=True
            )

    # -------------------------------------------------
    # RESET
    # -------------------------------------------------

    def reset(self) -> None:

        self.config = self.DEFAULT_CONFIG.copy()
        self.save()

    # -------------------------------------------------
    # EXISTS
    # -------------------------------------------------

    def exists(self) -> bool:

        return self.config_path.exists()

    # -------------------------------------------------
    # STRING
    # -------------------------------------------------

    def __repr__(self) -> str:

        return (
            f"ConfigManager("
            f"{self.config_path}"
            f")"
        )