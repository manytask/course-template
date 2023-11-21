from __future__ import annotations

from collections.abc import Generator
from dataclasses import dataclass
from typing import Any, Type

from ..configs import ParametersResolver, PipelineStageConfig
from ..exceptions import BadConfig, ExecutionFailedError
from ..plugins import PluginABC


@dataclass
class GlobalPipelineVariables:
    """Base variables passed in pipeline stages."""

    REF_DIR: str
    REPO_DIR: str
    TEMP_DIR: str
    TASK_NAMES: list[str]
    TASK_SUB_PATHS: list[str]


@dataclass
class TaskPipelineVariables:
    """Variables passed in pipeline stages for each task."""

    TASK_NAME: str
    TASK_SUB_PATH: str


@dataclass
class PipelineStageResult:
    failed: bool
    skipped: bool
    output: str


@dataclass
class PipelineResult:
    failed: bool
    stage_results: list[PipelineStageResult]


class PipelineRunner:
    """Class encapsulating the pipeline execution logic."""

    def __init__(
        self,
        pipeline: list[PipelineStageConfig],
        plugins: dict[str, Type[PluginABC]],
    ):
        """
        Init pipeline runner with predefined stages/plugins to use, parameters (placeholders) resolved later.
        :param pipeline: list of pipeline stages
        :param plugins: dict of plugins available to use
        :raises BadConfig: if plugin does not exist or does not support isolation (no placeholders are checked)
        """
        self.pipeline = pipeline
        self.plugins = plugins

        self.validate()

    def validate(self, parameters: dict[str, Any] | None = None) -> None:
        """
        Validate the pipeline configuration.
        :param parameters: parameters for placeholders (if None - no placeholders are checked)
        """
        parameters_resolver = ParametersResolver(parameters or {})

        for pipeline_stage in self.pipeline:
            # validate plugin exists
            if pipeline_stage.run not in self.plugins:
                raise BadConfig(f"Unknown plugin {pipeline_stage.run} in pipeline stage {pipeline_stage.name}")
            plugin = self.plugins[pipeline_stage.run]

            # check plugin supports isolation
            if pipeline_stage.isolate and not plugin.supports_isolation:
                raise BadConfig(f"Plugin {pipeline_stage.run} does not support isolation")

            # validate args of the plugin (first resolve placeholders)
            if parameters:
                resolved_args = parameters_resolver.resolve(pipeline_stage.args)
                plugin.validate_args(resolved_args)

            # validate run_if condition
            if parameters and pipeline_stage.run_if:
                resolved_run_if = parameters_resolver.resolve_single_string(pipeline_stage.run_if)
                if not isinstance(resolved_run_if, bool):
                    raise BadConfig(
                        f"Invalid run_if condition {pipeline_stage.run_if} in pipeline stage {pipeline_stage.name}"
                    )

    def run(self, parameters: dict[str, Any]) -> Generator[PipelineStageResult]:
        parameters_resolver = ParametersResolver(parameters)

        for pipeline_stage in self.pipeline:
            # resolve run condition if any; skip if run_if=False
            if pipeline_stage.run_if:
                resolved_run_if = parameters_resolver.resolve_single_string(pipeline_stage.run_if)
                if not resolved_run_if:
                    yield PipelineStageResult(
                        failed=False,
                        skipped=True,
                        output="",
                    )
                    continue

            # resolve placeholders in arguments
            resolved_args = parameters_resolver.resolve(pipeline_stage.args)

            # select the plugin to run
            plugin = self.plugins[pipeline_stage.run]

            # run the plugin with executor
            try:
                plugin.run(resolved_args)
            except ExecutionFailedError as e:
                yield PipelineStageResult(
                    failed=True,
                    skipped=False,
                    output=e.output,
                )
                if pipeline_stage.fail == PipelineStageConfig.FailType.FAST:
                    break

            yield PipelineStageResult(
                failed=False,
                skipped=False,
                output="",
            )
