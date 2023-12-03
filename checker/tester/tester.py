from __future__ import annotations

import tempfile
from collections.abc import Generator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..configs import CheckerTestingConfig
from ..configs.checker import CheckerStructureConfig, CheckerConfig
from ..course import Course, FileSystemTask
from ..exceptions import ExecutionFailedError, ExecutionTimeoutError, RunFailedError, TestingError
from .pipeline import PipelineRunner, GlobalPipelineVariables, TaskPipelineVariables, PipelineResult
from ..plugins import load_plugins
from ..utils import print_info, print_header_info


@dataclass
class TaskTestResult:
    """Result of the task testing."""

    failed: bool
    skipped: bool
    output: str


class Tester:
    """
    Class to encapsulate all testing logic.
    1. Create temporary directory
    2. Execute global pipeline
    3. Execute task pipeline for each task
    4. Collect results and return them
    5. Remove temporary directory
    """
    __test__ = False  # do not collect this class for pytest

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

        :param course: Course object for iteration with physical course
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
        self.global_pipeline = PipelineRunner(self.testing_config.global_pipeline, self.plugins, verbose=verbose)
        self.task_pipeline = PipelineRunner(self.testing_config.tasks_pipeline, self.plugins, verbose=verbose)

        self.repository_dir = self.course.repository_root
        self.reference_dir = self.course.reference_root
        self._temporary_dir_manager = tempfile.TemporaryDirectory()
        self.temporary_dir = Path(self._temporary_dir_manager.name)

        self.cleanup = cleanup
        self.verbose = verbose
        self.dry_run = dry_run

    def _get_global_pipeline_parameters(self, tasks: list[FileSystemTask]) -> dict[str, Any]:
        global_variables = GlobalPipelineVariables(
            REF_DIR=self.reference_dir.absolute().as_posix(),
            REPO_DIR=self.repository_dir.absolute().as_posix(),
            TEMP_DIR=self.temporary_dir.absolute().as_posix(),
            TASK_NAMES=[task.name for task in tasks],
            TASK_SUB_PATHS=[task.relative_path for task in tasks],
        )
        global_parameters = self.default_params.__dict__ | global_variables.__dict__
        return global_parameters

    def _get_task_pipeline_parameters(self, global_parameters: dict[str, Any], task: FileSystemTask) -> dict[str, Any]:
        task_variables = TaskPipelineVariables(
            TASK_NAME=task.name,
            TASK_SUB_PATH=task.relative_path,
        )
        task_specific_params = task.config.params if task.config and task.config.params else {}
        task_parameters = (
            global_parameters |
            task_specific_params |
            task_variables.__dict__
        )
        return task_parameters

    def validate(self) -> None:
        # get all tasks
        tasks = self.course.get_tasks(enabled=True)

        # validate global pipeline (only default params and variables available)
        print("- global pipeline...")
        global_parameters = self._get_global_pipeline_parameters(tasks)
        self.global_pipeline.validate(global_parameters)
        print("  ok")

        for task in tasks:
            # validate task with global + task-specific params
            print(f"- task {task.name} pipeline...")
            # check task parameter are
            task_parameters = self._get_task_pipeline_parameters(global_parameters, task)
            # TODO: read from config task specific pipeline
            self.task_pipeline.validate(task_parameters)
            print("  ok")

    def run(self) -> Generator[float]:
        # copy files for testing
        self.course.copy_files_for_testing(self.temporary_dir)

        # get all tasks
        tasks = self.course.get_tasks(enabled=True)

        # run global pipeline
        print_header_info("Run global pipeline:", color='pink')
        global_parameters = self._get_global_pipeline_parameters(tasks)
        global_pipeline_result: PipelineResult = self.global_pipeline.run(global_parameters, dry_run=self.dry_run)
        print_info(str(global_pipeline_result), color='pink')

        if not global_pipeline_result:
            raise TestingError("Global pipeline failed")

        for task in tasks:
            # run task pipeline
            print_header_info(f"Run <{task.name}> task pipeline:", color='pink')

            task_parameters = self._get_task_pipeline_parameters(global_parameters, task)
            # TODO: read from config task specific pipeline
            task_pipeline_result: PipelineResult = self.task_pipeline.run(task_parameters, dry_run=self.dry_run)
            # TODO: remove dry_run
            print_info(str(task_pipeline_result), color='pink')

    def __del__(self) -> None:
        # if self.cleanup:
        if self.__dict__.get("cleanup") and self._temporary_dir_manager:
            self._temporary_dir_manager.cleanup()
