from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .configs import TaskConfig, DeadlinesConfig
from .configs.checker import CheckerParametersConfig


@dataclass
class FileSystemTask:
    name: str
    relative_path: str
    config: TaskConfig | None = None


class Course:
    """
    Main point of the "physical" course.
    Class responsible for interaction with the file system directory.
    """

    def __init__(
        self,
        checker_config: CheckerParametersConfig,
        deadlines_config: DeadlinesConfig,
        repository_root: Path,
        reference_root: Path | None = None,
    ):
        self.checker = checker_config
        self.deadlines = deadlines_config

        self.repository_root = repository_root
        self.reference_root = reference_root or repository_root

        self.reference_tasks = self._search_for_tasks_by_configs(self.reference_root)
        self.repository_tasks = [
            task for task in self.reference_tasks if (self.repository_root / task.relative_path).exists()
        ]

    def _search_for_tasks_by_configs(self, root: Path) -> list[FileSystemTask]:
        for task_config_path in root.glob(f"**/.task.yml"):
            task_config = TaskConfig.from_yaml(task_config_path)
            yield FileSystemTask(
                name=task_config.name,
                relative_path=str(task_config_path.parent.relative_to(root)),
                config=task_config,
            )

    def list_all_public_files(self, root: Path) -> list[Path]:
        # read global files
        glob_patterns = self.checker.structure.public_patterns
        global_files = [file for pattern in glob_patterns for file in root.glob(pattern)]
        # remove all task directories, wi
        # filter with tasks specific configs
        task_files = [
            file
            for task in self.repository_tasks
            for pattern in task.config.structure.public_patterns
            for file in (root / task.relative_path).glob(pattern)
        ]

