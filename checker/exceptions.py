from __future__ import annotations

from dataclasses import dataclass


class CheckerException(Exception):
    """Base exception for Checker package"""

    __test__ = False  # to disable pytest detecting it as Test class
    pass


class ValidationError(CheckerException):
    """Base validation error of configs, project structure, etc."""

    pass


class BadConfig(ValidationError):
    """All configs exceptions: deadlines, checker and tasks configs"""

    pass


class BadStructure(ValidationError):
    """Course structure exception: some files are missing, etc."""

    pass


class ExportError(CheckerException):
    """Export stage exception"""

    pass


class ReportError(CheckerException):
    """Report stage exception"""

    pass


class TestingError(CheckerException):
    """All testers exceptions can occur during testing stage"""

    pass


@dataclass
class ExecutionFailedError(TestingError):
    """Execution failed exception"""

    message: str = ""
    output: str | None = None

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}: {self.message}"


class ExecutionTimeoutError(ExecutionFailedError):
    """Execution timeout exception"""

    pass


class RunFailedError(ExecutionFailedError):
    """Execution run failed exception (return code != 0)"""

    pass
