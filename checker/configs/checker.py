from __future__ import annotations

from enum import Enum

from pydantic import AnyUrl, Field, RootModel, ValidationError, field_validator

from .utils import CustomBaseModel, YamlLoaderMixin

ParamType = int | float | str | list[int | float | str | None] | None


class CheckerStructureConfig(CustomBaseModel):
    private_patterns: list[str] = Field(default_factory=list)
    public_patterns: list[str] = Field(default_factory=list)
    allow_to_change_patterns: list[str] = Field(default_factory=list)


class CheckerParametersConfig(RootModel):
    root: dict[str, ParamType]

    def __getitem__(self, item: str) -> ParamType:
        return self.root[item]


class CheckerExportConfig(CustomBaseModel):
    class TemplateType(Enum):
        SEARCH = "search"
        CREATE = "create"

    destination: AnyUrl
    default_branch: str = "main"
    commit_message: str = "chore(auto): export new tasks"
    templates: TemplateType = TemplateType.SEARCH


class CheckerManytaskConfig(CustomBaseModel):
    url: AnyUrl
    course: str


class PipelineStageConfig(CustomBaseModel):
    class FailType(Enum):
        FAST = "fast"
        AFTER_ALL = "after_all"
        NEVER = "never"

    name: str
    run: str

    args: dict[str, ParamType] = Field(default_factory=dict)

    run_if: str | None = None
    fail: FailType = FailType.FAST
    isolate: bool = True


class CheckerTestingConfig(CustomBaseModel):
    class ChangesDetectionType(Enum):
        BRANCH_NAME = "branch_name"
        COMMIT_MESSAGE = "commit_message"
        LAST_COMMIT_CHANGES = "last_commit_changes"
        FILES_CHANGED = "files_changed"

    class ExecutorType(Enum):
        # DOCKER = 'docker'
        SANDBOX = "sandbox"
        MINIJAIL = "minijail"

    changes_detection: ChangesDetectionType = ChangesDetectionType.LAST_COMMIT_CHANGES
    executor: ExecutorType = ExecutorType.MINIJAIL

    search_plugins: list[str] = Field(default_factory=list)

    global_pipeline: list[PipelineStageConfig] = Field(default_factory=list)
    tasks_pipeline: list[PipelineStageConfig] = Field(default_factory=list)


class CheckerConfig(CustomBaseModel, YamlLoaderMixin):
    """
    Checker configuration.
    :ivar version: config version
    :ivar params: default parameters for task pipeline
    :ivar structure: describe the structure of the repo - private/public and allowed for change files
    :ivar export: describe export (publishing to public repo)
    :ivar manytask: describe connection to manytask
    :ivar testing: describe testing/checking - pipeline, isolation etc
    """

    version: int

    params: CheckerParametersConfig = Field(default_factory=dict)

    structure: CheckerStructureConfig
    export: CheckerExportConfig
    manytask: CheckerManytaskConfig
    testing: CheckerTestingConfig

    @field_validator("version")
    @classmethod
    def check_version(cls, v: int) -> None:
        if v != 1:
            raise ValidationError(f"Only version 1 is supported for {cls.__name__}")
