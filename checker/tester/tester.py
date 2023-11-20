from __future__ import annotations

import tempfile
from collections.abc import Generator
from pathlib import Path
from typing import Any

from ..configs import CheckerTestingConfig
from ..configs.checker import CheckerStructureConfig, CheckerConfig
from ..course import Course
from ..exceptions import ExecutionFailedError, ExecutionTimeoutError, RunFailedError
from .pipeline import PipelineRunner, GlobalPipelineVariables, TaskPipelineVariables
from ..plugins import load_plugins


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
        course: Course,
        checker_config: CheckerConfig,
        *,
        cleanup: bool = True,
        verbose: bool = False,
        dry_run: bool = False,
    ):
        """
        Init tester in specific public and private dirs.

        :
        :param checker_config: Full checker config with testing,structure and params folders
        :param cleanup: Cleanup temporary directory after testing
        :param verbose: Whatever to print private outputs and debug info
        :param dry_run: Do not execute anything, just print what would be executed
        :raises exception.ValidationError: if config is invalid or repo structure is wrong
        """
        self.course = course

        self.testing_config = checker_config.testing
        self.structure_config = checker_config.structure
        self.default_params = checker_config.params

        self.plugins = load_plugins(self.testing_config.search_plugins, verbose=verbose)
        self.global_pipeline = PipelineRunner(self.testing_config.global_pipeline, self.plugins)
        self.task_pipeline = PipelineRunner(self.testing_config.task_pipeline, self.plugins)

        self.repository_dir = self.course.repository_root
        self.reference_dir = self.course.reference_root
        self._temporary_dir_manager = tempfile.TemporaryDirectory()
        self.temporary_dir = Path(self._temporary_dir_manager.name)

        self.cleanup = cleanup
        self.verbose = verbose
        self.dry_run = dry_run

    def validate(self) -> None:
        # validate global pipeline (only default params and variables available)
        global_variables = GlobalPipelineVariables(
            REF_DIR=self.reference_dir.absolute().as_posix(),
            REPO_DIR=self.repository_dir.absolute().as_posix(),
            TEMP_DIR=self.temporary_dir.absolute().as_posix(),
            TASK_NAMES=[task.name for task in self.course.tasks],
            TASK_SUB_PATHS=[task.relative_path for task in self.course.tasks],
        )
        global_parameters = self.default_params.__dict__ | global_variables.__dict__
        self.global_pipeline.validate(global_parameters)

        for task in self.course.tasks:
            # validate task with global + task-specific params
            task_variables = TaskPipelineVariables(
                TASK_NAME=task.name,
                TASK_SUB_PATH=task.relative_path,
            )
            task_parameters = (
                self.default_params.__dict__ | task.parameters | global_variables.__dict__ | task_variables.__dict__
            )
            self.task_pipeline.validate(task_parameters)

    def run(self) -> Generator[float]:
        # run global pipeline
        print("Running global pipeline")

        for task in self.course.tasks:
            # run task pipeline
            print(f"Running pipeline for <{task.name}> task")

    def __del__(self) -> None:
        if self.cleanup:
            self._temporary_dir_manager.cleanup()
