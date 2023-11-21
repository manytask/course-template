from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .configs import TaskConfig, DeadlinesConfig
from .configs.checker import CheckerParametersConfig, CheckerConfig
from .exceptions import BadConfig


@dataclass
class FileSystemTask:
    name: str
    relative_path: str
    config: TaskConfig | None = None


@dataclass
class FileSystemGroup:
    name: str
    relative_path: str
    tasks: list[FileSystemTask]


class Course:
    """
    Main point of the "physical" course.
    Class responsible for interaction with the file system directory.
    """

    def __init__(
        self,
        checker_config: CheckerConfig,
        deadlines_config: DeadlinesConfig,
        repository_root: Path,
        reference_root: Path | None = None,
    ):
        self.checker = checker_config
        self.deadlines = deadlines_config

        self.repository_root = repository_root
        self.reference_root = reference_root or repository_root

        self.potential_groups = {group.name: group for group in self._search_potential_groups(self.repository_root)}
        self.potential_tasks = {task.name: task for group in self.potential_groups.values() for task in group.tasks}

    def validate(self) -> None:
        # check all groups and tasks mentioned in deadlines exists
        deadlines_groups = self.deadlines.get_groups(enabled=True)
        for deadline_group in deadlines_groups:
            if deadline_group.name not in self.potential_groups:
                raise BadConfig(f"Group {deadline_group.name} not found in repository")

        deadlines_tasks = self.deadlines.get_tasks(enabled=True)
        for deadlines_task in deadlines_tasks:
            if deadlines_task.name not in self.potential_tasks:
                raise BadConfig(f"Task {deadlines_task.name} of not found in repository")

    def get_groups(
            self,
            enabled: bool | None = None,
    ) -> list[FileSystemGroup]:
        return [
            self.potential_groups[deadline_group.name]
            for deadline_group in self.deadlines.get_groups(enabled=enabled)
            if deadline_group.name in self.potential_groups
        ]

    def get_tasks(
            self,
            enabled: bool | None = None,
    ) -> list[FileSystemTask]:
        return [
            self.potential_tasks[deadline_task.name]
            for deadline_task in self.deadlines.get_tasks(enabled=enabled)
            if deadline_task.name in self.potential_tasks
        ]

    def _search_potential_groups(self, root: Path) -> list[FileSystemGroup]:
        # search in the format $GROUP_NAME/$TASK_NAME starting root
        potential_groups = []

        for group_path in root.iterdir():
            if not group_path.is_dir():
                continue

            potential_tasks = []

            for task_path in group_path.iterdir():
                if not task_path.is_dir():
                    continue

                task_config_path = task_path / ".task.yml"
                task_config: TaskConfig | None = None
                if task_config_path.exists():
                    try:
                        task_config = TaskConfig.from_yaml(task_config_path)
                    except BadConfig as e:
                        raise BadConfig(f"Task config {task_config_path} is invalid:\n{e}")

                potential_tasks.append(
                    FileSystemTask(
                        name=task_path.name,
                        relative_path=str(task_path.relative_to(root)),
                        config=task_config,
                    )
                )

            potential_groups.append(
                FileSystemGroup(
                    name=group_path.name,
                    relative_path=str(group_path.relative_to(root)),
                    tasks=potential_tasks,
                )
            )
        return potential_groups

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

