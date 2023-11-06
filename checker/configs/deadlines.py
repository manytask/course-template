from __future__ import annotations

from datetime import datetime, timedelta
from enum import Enum

from pydantic import Field, validator, field_validator, ValidationError, model_validator

from .utils import YamlLoaderMixin, CustomBaseModel
from ..exceptions import BadConfig


class DeadlinesType(Enum):
    HARD = 'hard'
    INTERPOLATE = 'interpolate'


class DeadlinesSettingsConfig(CustomBaseModel):
    timezone: str
    deadlines: DeadlinesType = Field(default=DeadlinesType.HARD)
    max_submissions: int | None = None
    submission_penalty: float = 0

    @field_validator('max_submissions')
    @classmethod
    def check_max_submissions(cls, data: int | None) -> int | None:
        if data is not None and data <= 0:
            raise ValueError('max_submissions should be positive')
        return data


class DeadlinesTaskConfig(CustomBaseModel):
    task: str

    enabled: bool = True
    tags: list[str] = Field(default_factory=list)

    score: int
    bonus: int = 0
    special: int = 0

    @property
    def name(self) -> str:
        return self.task


class DeadlinesGroupConfig(CustomBaseModel):
    group: str

    enabled: bool = True
    tags: list[str] = []

    start: datetime
    steps: dict[float, datetime | timedelta] = Field(default_factory=dict)
    end: datetime | timedelta = None

    tasks: list[DeadlinesTaskConfig] = Field(default_factory=list)

    @property
    def name(self) -> str:
        return self.group

    @model_validator(mode='after')
    def check_dates(self) -> 'DeadlinesGroupConfig':
        # check end
        if isinstance(self.end, timedelta) and self.end < timedelta():
            raise ValueError(f'end timedelta <{self.end}> should be positive')
        if isinstance(self.end, datetime) and self.end < self.start:
            raise ValueError(f'end datetime <{self.end}> should be after the start <{self.start}>')

        # check steps
        last_step_date_or_delta = self.start
        for _, date_or_delta in self.steps.items():
            step_date = self.start + date_or_delta if isinstance(date_or_delta, timedelta) else date_or_delta
            last_step_date = self.start + last_step_date_or_delta if isinstance(last_step_date_or_delta, timedelta) else last_step_date_or_delta

            if isinstance(date_or_delta, timedelta) and date_or_delta < timedelta():
                raise ValueError(f'step timedelta <{date_or_delta}> should be positive')
            if isinstance(date_or_delta, datetime) and date_or_delta <= self.start:
                raise ValueError(f'step datetime <{date_or_delta}> should be after the start {self.start}')

            if step_date <= last_step_date:
                raise ValueError(f'step datetime/timedelta <{date_or_delta}> should be after the last step <{last_step_date_or_delta}>')
            last_step_date_or_delta = date_or_delta

        return self


class DeadlinesConfig(CustomBaseModel, YamlLoaderMixin):
    """Deadlines configuration."""
    version: int

    settings: DeadlinesSettingsConfig
    schedule: list[DeadlinesGroupConfig]

    @field_validator('version')
    @classmethod
    def check_version(cls, data: int) -> int:
        if data != 1:
            raise ValueError(f'Only version 1 is supported for {cls.__name__}')
        return data

    @field_validator('schedule')
    @classmethod
    def check_groups_unique(cls, data: list[DeadlinesGroupConfig]) -> list[DeadlinesGroupConfig]:
        groups = [group.name for group in data]
        duplicates = [name for name in groups if groups.count(name) > 1]
        if duplicates:
            raise ValueError(f'Group names should be unique, duplicates: {duplicates}')
        return data

    @field_validator('schedule')
    @classmethod
    def check_tasks_unique(cls, data: list[DeadlinesGroupConfig]) -> list[DeadlinesGroupConfig]:
        tasks_names = [task.name for group in data for task in group.tasks]
        duplicates = [name for name in tasks_names if tasks_names.count(name) > 1]
        if duplicates:
            raise ValueError(f'Task names should be unique, duplicates: {duplicates}')
        return data
