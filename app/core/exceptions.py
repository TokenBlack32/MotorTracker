"""
app/core/exceptions.py

MotorTracker
Custom Exceptions
"""


class MotorTrackerError(Exception):
    """
    Excepción base para toda la aplicación.
    """

    def __init__(self, message: str = "MotorTracker Error") -> None:
        super().__init__(message)


# ==========================================================
# CONFIGURATION
# ==========================================================

class ConfigurationError(MotorTrackerError):
    """
    Error relacionado con la configuración.
    """

    pass


class InvalidConfigurationError(ConfigurationError):
    """
    Configuración inválida.
    """

    pass


class ConfigurationFileNotFoundError(ConfigurationError):
    """
    No existe config.json.
    """

    pass


# ==========================================================
# FILES
# ==========================================================

class FileManagerError(MotorTrackerError):
    """
    Error del administrador de archivos.
    """

    pass


class FileNotFoundErrorMT(FileManagerError):
    """
    Archivo no encontrado.
    """

    pass


class FolderNotFoundError(FileManagerError):
    """
    Carpeta inexistente.
    """

    pass


class InvalidFileExtensionError(FileManagerError):
    """
    Extensión no soportada.
    """

    pass


# ==========================================================
# REPORTS
# ==========================================================

class ReportError(MotorTrackerError):
    """
    Error general de reportes.
    """

    pass


class ReportNotFoundError(ReportError):
    """
    No se encontró ningún reporte.
    """

    pass


class ReportReadError(ReportError):
    """
    Error al leer el reporte.
    """

    pass


class InvalidReportFormatError(ReportError):
    """
    Formato de reporte inválido.
    """

    pass


# ==========================================================
# DATABASE
# ==========================================================

class DatabaseError(MotorTrackerError):
    """
    Error de base de datos.
    """

    pass


class DatabaseNotFoundError(DatabaseError):
    """
    Base de datos inexistente.
    """

    pass


class DatabaseWriteError(DatabaseError):
    """
    Error escribiendo Excel.
    """

    pass


class DatabaseReadError(DatabaseError):
    """
    Error leyendo Excel.
    """

    pass


# ==========================================================
# IMPORT
# ==========================================================

class ImportErrorMT(MotorTrackerError):
    """
    Error durante la importación.
    """

    pass


class DuplicateRecordError(ImportErrorMT):
    """
    Registro duplicado.
    """

    pass


class MappingError(ImportErrorMT):
    """
    Error durante el mapeo de columnas.
    """

    pass


class ImportCancelledError(ImportErrorMT):
    """
    Importación cancelada.
    """

    pass


# ==========================================================
# VALIDATION
# ==========================================================

class ValidationError(MotorTrackerError):
    """
    Error de validación.
    """

    pass


class MissingColumnError(ValidationError):
    """
    Falta una columna requerida.
    """

    pass


class InvalidValueError(ValidationError):
    """
    Valor inválido.
    """

    pass


# ==========================================================
# BACKUP
# ==========================================================

class BackupError(MotorTrackerError):
    """
    Error creando respaldo.
    """

    pass


# ==========================================================
# LOGGER
# ==========================================================

class LoggerError(MotorTrackerError):
    """
    Error del sistema de logs.
    """

    pass


# ==========================================================
# UI
# ==========================================================

class UIError(MotorTrackerError):
    """
    Error de interfaz.
    """

    pass


# ==========================================================
# WATCHDOG
# ==========================================================

class WatcherError(MotorTrackerError):
    """
    Error del monitor de carpetas.
    """

    pass