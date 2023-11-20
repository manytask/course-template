from __future__ import annotations

from pydantic import Field

from .checker import CheckerParametersConfig, CheckerStructureConfig, PipelineStageConfig
from .utils import CustomBaseModel, YamlLoaderMixin


class TaskConfig(CustomBaseModel, YamlLoaderMixin):
    """Task configuration file."""

    version: int

    structure: CheckerStructureConfig | None = None
    parameters: CheckerParametersConfig | None = None
    task_pipeline: list[PipelineStageConfig] | None = None
