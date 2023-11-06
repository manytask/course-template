from __future__ import annotations

from datetime import datetime, timedelta
from enum import Enum
from typing import Union

from pydantic import Field, validator, field_validator, ValidationError, AnyUrl

from .utils import YamlLoaderMixin, CustomBaseModel
from ..exceptions import BadConfig


ParamType = int | float | str | list[int | float | str | None] | None


class CheckerStructureConfig(CustomBaseModel):
    private_patterns: list[str]
    public_patterns: list[str]
    allow_to_change_patterns: list[str]


class CheckerExportConfig(CustomBaseModel):
    class TemplateType(Enum):
        SEARCH = 'search'
        CREATE = 'create'

    destination: AnyUrl
    default_branch: str = 'main'
    commit_message: str = 'chore(auto): export new tasks'
    templates: TemplateType = TemplateType.SEARCH
    templates


class CheckerManytaskConfig(CustomBaseModel):
    url: AnyUrl
    course: str




class PipelineStageConfig(CustomBaseModel):
    class FailType(Enum):
        FAST = 'fast'
        AFTER_ALL = 'after_all'
        NEVER = 'never'

    name: str
    run: str

    args: dict[str, ParamType] = Field(default_factory=dict)

    run_if: str | None = None
    fail: FailType = FailType.FAST
    isolate: bool = True


class CheckerTestingConfig(CustomBaseModel):

    class ChangesDetectionType(Enum):
        BRANCH_NAME = 'branch_name'
        COMMIT_MESSAGE = 'commit_message'
        LAST_COMMIT_CHANGES = 'last_commit_changes'
        FILES_CHANGED = 'files_changed'

    class ExecutorType(Enum):
        # DOCKER = 'docker'
        SANDBOX = 'sandbox'
        MINIJAIL = 'minijail'

    changes_detection: ChangesDetectionType = ChangesDetectionType.LAST_COMMIT_CHANGES
    executor: ExecutorType = ExecutorType.MINIJAIL

    search_plugins: list[str] = Field(default_factory=list)

    global_pipeline: list[PipelineStageConfig] = Field(default_factory=list)
    tasks_pipeline: list[PipelineStageConfig] = Field(default_factory=list)


class CheckerConfig(CustomBaseModel, YamlLoaderMixin):
    """Checker configuration."""
    version: int

    params: dict[str, ParamType] = Field(default_factory=dict)

    structure: CheckerStructureConfig
    export: CheckerExportConfig
    manytask: CheckerManytaskConfig
    testing: CheckerTestingConfig

    @field_validator('version')
    @classmethod
    def check_version(cls, v: int) -> None:
        if v != 1:
            raise ValidationError(f'Only version 1 is supported for {cls.__name__}')