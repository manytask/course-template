from __future__ import annotations

import os
import sys
from pathlib import Path

import click
import yaml
from pydantic import ValidationError

from .tester.pipeline import PipelineRunner
from .plugins import load_plugins
from .exceptions import BadConfig
from .configs import DeadlinesConfig, CheckerConfig


ClickReadableFile = click.Path(exists=True, file_okay=True, readable=True, path_type=Path)
ClickReadableDirectory = click.Path(exists=True, file_okay=False, readable=True, path_type=Path)
ClickWritableDirectory = click.Path(file_okay=False, writable=True, path_type=Path)


@click.group(context_settings={"show_default": True})
@click.option(
    "--checker-config", type=ClickReadableFile, default=".checker.yml", help="Path to the checker config file."
)
@click.option(
    "--deadlines-config", type=ClickReadableFile, default=".deadlines.yml", help="Path to the deadlines config file."
)
@click.version_option(package_name="manytask-checker")
@click.pass_context
def cli(
    ctx: click.Context,
    checker_config: Path,
    deadlines_config: Path,
) -> None:
    """Manytask checker - automated tests for students' assignments."""
    ctx.ensure_object(dict)
    ctx.obj = {
        'course_config_path': checker_config,
        'deadlines_config_path': deadlines_config,
    }


@cli.command()
@click.argument("root", type=ClickReadableDirectory, default=".")
@click.option('-v/-s', '--verbose/--silent', is_flag=True, default=True, help='Verbose output')
@click.pass_context
def validate(
    ctx: click.Context,
    root: Path,
    verbose: bool,
):
    """
    Validate the configuration files, plugins and tasks.
    1. Validate the configuration files content.
    2. Validate mentioned plugins.
    3. Check all tasks are valid and consistent with the deadlines.
    """

    print('Validating configuration files...')
    try:
        checker_config = CheckerConfig.from_yaml(ctx.obj['course_config_path'])
        deadlines_config = DeadlinesConfig.from_yaml(ctx.obj['deadlines_config_path'])
    except BadConfig as e:
        print('Configuration Failed')
        print(e)
        exit(1)
    print('Ok')

    print('Loading plugins...')
    try:
        plugins = load_plugins(checker_config.testing.search_plugins)
        print(f'Loaded {len(plugins)} plugins\n', plugins)
    except BadConfig as e:
        print('Plugin Loading Failed')
        print(e)
        exit(1)
    print('Ok')

    print('Validating global pipeline...')
    try:
        pipeline = PipelineRunner(checker_config.testing.tasks_pipeline, plugins)
        pipeline.validate(parameters=None)  # TODO: add parameters
    except BadConfig as e:
        print('Pipeline Validation Failed')
        print(e)
        exit(1)
    print('Ok')

    print('Searching tasks...')
    file_tasks_folders = [task.parent for task in root.glob('**/.task.yml') if task.is_file()]
    print(f'Found {len(file_tasks_folders)} tasks')

    print('Validating tasks...')




@cli.command()
@click.argument("root", type=ClickReadableDirectory, default=".")
@click.option('-t', '--task', type=str, multiple=True, default=None, help='Task name to check (multiple possible)')
@click.option('-g', '--group', type=str, multiple=True, default=None, help='Group name to check (multiple possible)')
@click.option('--no-clean', is_flag=True, help='Clean or not check tmp folders')
@click.option('-p', '--parallelize', is_flag=True, default=True, help='Execute parallel checking of tasks')
@click.option('-n', '--num-processes', type=int, default=os.cpu_count(), help='Num of processes parallel checking')
@click.option('-v/-s', '--verbose/--silent', is_flag=True, default=True, help='Verbose tests output')
@click.option('--dry-run', is_flag=True, help='Do not execute anything, only log actions')
@click.pass_context
def check(
    ctx: click.Context,
    root: Path,
    task: list[str] | None,
    group: list[str] | None,
    no_clean: bool,
    parallelize: bool,
    num_processes: int,
    verbose: bool,
    dry_run: bool,
):
    """Check private repository: run tests, lint etc. First forces validation."""

    ctx.invoke(validate, ctx=ctx, root=root, verbose=verbose)


    checker_config = CheckerConfig.from_yaml(ctx.obj['course_config_path'])
    deadlines_config = DeadlinesConfig.from_yaml(ctx.obj['deadlines_config_path'])

    # TODO: progressbar on paralelize

    try:
        config_data = yaml.safe_load(Path(config_path).read_text())
        config = Config.parse_obj(config_data)
        # Your logic to 'check' based on the configuration goes here.
        click.echo("Checks completed successfully.")
    except Exception as e:
        click.echo(f"An error occurred during the checks: {e}")


@cli.command()
@click.pass_context
def grade(config_path):
    """
    Process the configuration file and grade the tasks.
    """
    try:
        config_data = yaml.safe_load(Path(config_path).read_text())
        config = Config.parse_obj(config_data)
        # Your logic to 'grade' based on the configuration goes here.
        click.echo("Grading completed successfully.")
    except Exception as e:
        click.echo(f"An error occurred during grading: {e}")


if __name__ == "__main__":
    cli()
