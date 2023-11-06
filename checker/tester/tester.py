from __future__ import annotations

import tempfile
from typing import Any

from .pipeline import PipelineRunner
from ..configs import CheckerTestingConfig
from ..exceptions import ExecutionFailedError, RunFailedError, ExecutionTimeoutError


class Tester:
    """
    Class to encapsulate all testing logic.
    1. Create temporary directory
    2. Execute global pipeline
    3. Execute task pipeline for each task
    4. Collect results and return them
    5. Remove temporary directory
    """

    def __init__(
            self,
            testing_config: CheckerTestingConfig,
            default_params: dict[str, Any] | None = None,
            *,
            cleanup: bool = True,
            verbose: bool = False,
            dry_run: bool = False,
    ):
        """
        Init tester with config and default parameters.
        :param testing_config: Testing config with pipeline and plugins
        :param default_params: Default parameters to use in pipeline
        :param cleanup: Cleanup temporary directory after testing
        :param verbose: Whatever to print private outputs and debug info
        :param dry_run: Do not execute anything, just print what would be executed
        :raises exception.ValidationError: if config is invalid
        """
        self.config = testing_config
        self.default_params = default_params or {}

        self.cleanup = cleanup
        self.verbose = verbose
        self.dry_run = dry_run

    def __call__(self) -> None:
        return self
