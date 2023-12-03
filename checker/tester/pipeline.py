from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Type

from ..configs import ParametersResolver, PipelineStageConfig
from ..exceptions import BadConfig, ExecutionFailedError
from ..plugins import PluginABC
from ..utils import print_info


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
    name: str
    failed: bool
    skipped: bool
    percentage: float = 0.0
    output: str = ''

    def __str__(self) -> str:
        return f"PipelineStageResult: failed={int(self.failed)}, skipped={int(self.skipped)}, percentage={self.percentage:.2f}, name='{self.name}'"


@dataclass
class PipelineResult:
    failed: bool
    stage_results: list[PipelineStageResult]

    def __str__(self) -> str:
        return f'PipelineResult: failed={int(self.failed)}\n' + '\n'.join([f'  {stage_result}' for stage_result in self.stage_results])


class PipelineRunner:
    """Class encapsulating the pipeline execution logic."""

    def __init__(
        self,
        pipeline: list[PipelineStageConfig],
        plugins: dict[str, Type[PluginABC]],
        *,
        verbose: bool = False,
    ):
        """
        Init pipeline runner with predefined stages/plugins to use, parameters (placeholders) resolved later.
        :param pipeline: list of pipeline stages
        :param plugins: dict of plugins available to use
        :param verbose: if True, print more debug info for teachers
        :raises BadConfig: if plugin does not exist or does not support isolation (no placeholders are checked)
        """
        self.pipeline = pipeline
        self.plugins = plugins

        self.verbose = verbose

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
            plugin_class = self.plugins[pipeline_stage.run]

            # validate args of the plugin (first resolve placeholders)
            if parameters:
                resolved_args = parameters_resolver.resolve(pipeline_stage.args)
                plugin_class.validate(resolved_args)

            # validate run_if condition
            if parameters and pipeline_stage.run_if:
                resolved_run_if = parameters_resolver.resolve_single_string(pipeline_stage.run_if)
                if not isinstance(resolved_run_if, bool):
                    raise BadConfig(
                        f"Invalid run_if condition {pipeline_stage.run_if} in pipeline stage {pipeline_stage.name}"
                    )

    def run(self, parameters: dict[str, Any], *, dry_run: bool = False) -> PipelineResult:
        parameters_resolver = ParametersResolver(parameters)

        pipeline_stage_results = []
        pipeline_passed = True
        skip_the_rest = False
        for pipeline_stage in self.pipeline:
            # resolve placeholders in arguments
            resolved_args = parameters_resolver.resolve(pipeline_stage.args)
            resolved_run_if = parameters_resolver.resolve_single_string(pipeline_stage.run_if) if pipeline_stage.run_if else None

            print_info(f'-> Running "{pipeline_stage.name}" stage:', color='orange')
            if self.verbose:
                print_info(f'    run_if: {pipeline_stage.run_if}', color='grey')
                print_info(f'    resolved_run_if: {resolved_run_if}', color='grey')
                print_info(f'    fail: {pipeline_stage.fail}', color='grey')
                print_info(f'    run: {pipeline_stage.run}', color='grey')
                print_info(f'    args: {pipeline_stage.args}', color='grey')
                print_info(f'    resolved_args: {resolved_args}', color='grey')

            # skip the rest of stages if failed before
            if skip_the_rest:
                print_info('skipped! (got error above)', color='blue')
                pipeline_stage_results.append(PipelineStageResult(
                    name=pipeline_stage.name,
                    failed=False,
                    skipped=True,
                ))
                continue

            # resolve run condition if any; skip if run_if=False
            if pipeline_stage.run_if:
                if not resolved_run_if:
                    print_info(f'skipped! (run_if={resolved_run_if})', color='blue')
                    pipeline_stage_results.append(PipelineStageResult(
                        name=pipeline_stage.name,
                        failed=False,
                        skipped=True,
                    ))
                    continue

            # select the plugin to run
            plugin_class = self.plugins[pipeline_stage.run]
            plugin = plugin_class()

            # skip if dry run
            if dry_run:
                print_info('[output here]')
                print_info('dry run!', color='blue')
                pipeline_stage_results.append(PipelineStageResult(
                    name=pipeline_stage.name,
                    failed=False,
                    skipped=False,
                    percentage=1.0,
                ))
                continue

            # run the plugin with executor
            try:
                output = plugin.run(resolved_args)
                print_info(output or '[empty output]')
                print_info('ok!', color='green')
                pipeline_stage_results.append(PipelineStageResult(
                    name=pipeline_stage.name,
                    failed=False,
                    skipped=False,
                    output=output,
                    percentage=1.0,  # TODO: get percentage from plugin
                ))
            except ExecutionFailedError as e:
                print_info(e.output or '[empty output]')
                print_info('error!', color='red')
                pipeline_stage_results.append(PipelineStageResult(
                    name=pipeline_stage.name,
                    failed=True,
                    skipped=False,
                    output=e.output or '',
                    percentage=0.0,  # TODO: get percentage from plugin
                ))
                if pipeline_stage.fail == PipelineStageConfig.FailType.FAST:
                    skip_the_rest = True
                    pipeline_passed = False
                elif pipeline_stage.fail == PipelineStageConfig.FailType.AFTER_ALL:
                    pipeline_passed = False
                elif pipeline_stage.fail == PipelineStageConfig.FailType.NEVER:
                    pass
                else:
                    assert False, f"Unknown fail type {pipeline_stage.fail}"

        return PipelineResult(
            failed=not pipeline_passed,
            stage_results=pipeline_stage_results,
        )
