"""Morphix normalized error and exception hierarchy."""


class MorphixError(Exception):
    """Base exception for all Morphix errors."""
    def __init__(self, message: str, details: str = "", code: str = "ERR_MORPHIX"):
        super().__init__(message)
        self.message = message
        self.details = details
        self.code = code

    def to_dict(self):
        return {
            "code": self.code,
            "message": self.message,
            "details": self.details
        }


class EngineNotFoundError(MorphixError):
    """Raised when a conversion requires an engine that is not installed or detected."""
    def __init__(self, engine_name: str, install_hint: str = ""):
        msg = f"Required engine '{engine_name}' is not installed or available."
        hint = install_hint or f"Please install {engine_name} or configure its executable path in Settings."
        super().__init__(msg, details=hint, code="ERR_ENGINE_NOT_FOUND")
        self.engine_name = engine_name


class FormatNotSupportedError(MorphixError):
    """Raised when an input or output format is not supported or no conversion route exists."""
    def __init__(self, source_fmt: str, target_fmt: str, reason: str = ""):
        msg = f"Conversion from '{source_fmt}' to '{target_fmt}' is not supported."
        details = reason or "No valid conversion route could be planned with the available engines."
        super().__init__(msg, details=details, code="ERR_FORMAT_NOT_SUPPORTED")
        self.source_fmt = source_fmt
        self.target_fmt = target_fmt


class ConversionFailedError(MorphixError):
    """Raised when a conversion operation fails during execution."""
    def __init__(self, message: str, stderr: str = "", exit_code: int = -1):
        super().__init__(message, details=stderr, code="ERR_CONVERSION_FAILED")
        self.stderr = stderr
        self.exit_code = exit_code


class ValidationError(MorphixError):
    """Raised when an output file fails validation."""
    def __init__(self, message: str, details: str = ""):
        super().__init__(message, details=details, code="ERR_VALIDATION_FAILED")


class SecurityError(MorphixError):
    """Raised when a potential security violation is detected (e.g. path traversal)."""
    def __init__(self, message: str, details: str = ""):
        super().__init__(message, details=details, code="ERR_SECURITY_VIOLATION")


class JobCancelledError(MorphixError):
    """Raised when a running or queued job is cancelled."""
    def __init__(self, job_id: str):
        super().__init__(f"Job '{job_id}' was cancelled by the user.", code="ERR_JOB_CANCELLED")
        self.job_id = job_id
