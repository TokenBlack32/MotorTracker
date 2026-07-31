"""
app/utils/logger.py

MotorTracker
Logger Manager
"""

from __future__ import annotations

import sys
import time
from functools import wraps
from pathlib import Path
from typing import Callable, Any

from loguru import logger

from app.core.config_manager import ConfigManager


class LoggerManager:
    """
    Administrador centralizado de logs.

    Toda la aplicación utilizará esta clase.
    """

    _configured = False

    @classmethod
    def setup(cls) -> None:

        if cls._configured:
            return

        config = ConfigManager()

        log_folder = Path(config.get("logs.folder"))
        log_folder.mkdir(parents=True, exist_ok=True)

        logger.remove()

        # Consola
        logger.add(
            sys.stdout,
            level=config.get("logs.level", "INFO"),
            colorize=True,
            format=(
                "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
                "<level>{level: <8}</level> | "
                "<cyan>{name}</cyan>:"
                "<cyan>{function}</cyan>:"
                "<cyan>{line}</cyan> | "
                "<level>{message}</level>"
            )
        )

        # Archivo
        logger.add(
            log_folder / "motortracker.log",
            level=config.get("logs.level", "INFO"),
            rotation="5 MB",
            retention="30 days",
            compression="zip",
            enqueue=True,
            encoding="utf-8",
            format=(
                "{time:YYYY-MM-DD HH:mm:ss} | "
                "{level:<8} | "
                "{name}:{function}:{line} | "
                "{message}"
            )
        )

        cls._configured = True

    @staticmethod
    def debug(message: str) -> None:
        logger.debug(message)

    @staticmethod
    def info(message: str) -> None:
        logger.info(message)

    @staticmethod
    def warning(message: str) -> None:
        logger.warning(message)

    @staticmethod
    def error(message: str) -> None:
        logger.error(message)

    @staticmethod
    def critical(message: str) -> None:
        logger.critical(message)

    @staticmethod
    def exception(message: str) -> None:
        logger.exception(message)


# ==========================================================
# DECORADORES
# ==========================================================

def log_execution(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Registra automáticamente la ejecución de una función.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):

        LoggerManager.info(f"Iniciando: {func.__name__}")

        start = time.perf_counter()

        try:

            result = func(*args, **kwargs)

            elapsed = time.perf_counter() - start

            LoggerManager.info(
                f"Finalizado: {func.__name__} "
                f"({elapsed:.3f}s)"
            )

            return result

        except Exception:

            LoggerManager.exception(
                f"Error ejecutando {func.__name__}"
            )

            raise

    return wrapper


# ==========================================================
# DECORADOR DE TIEMPO
# ==========================================================

def measure_time(func: Callable[..., Any]) -> Callable[..., Any]:

    @wraps(func)
    def wrapper(*args, **kwargs):

        start = time.perf_counter()

        result = func(*args, **kwargs)

        elapsed = time.perf_counter() - start

        LoggerManager.info(
            f"{func.__name__} tardó "
            f"{elapsed:.4f} segundos"
        )

        return result

    return wrapper


# ==========================================================
# DECORADOR DE ERRORES
# ==========================================================

def catch_exceptions(func: Callable[..., Any]) -> Callable[..., Any]:

    @wraps(func)
    def wrapper(*args, **kwargs):

        try:

            return func(*args, **kwargs)

        except Exception:

            LoggerManager.exception(
                f"Excepción en {func.__name__}"
            )

            raise

    return wrapper


# ==========================================================
# LOG DE IMPORTACIÓN
# ==========================================================

class ImportLogger:

    @staticmethod
    def start(filename: str) -> None:

        LoggerManager.info(
            f"========== IMPORTACIÓN =========="
        )

        LoggerManager.info(
            f"Archivo: {filename}"
        )

    @staticmethod
    def finish(
        imported: int,
        duplicates: int,
        errors: int
    ) -> None:

        LoggerManager.info(
            f"Importados : {imported}"
        )

        LoggerManager.info(
            f"Duplicados : {duplicates}"
        )

        LoggerManager.info(
            f"Errores    : {errors}"
        )

        LoggerManager.info(
            "================================"
        )