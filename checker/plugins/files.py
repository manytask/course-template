from .base import PluginABC


class CopyFilesPlugin(PluginABC):
    """Plugin for copying files."""

    name = "copy_files"
    supports_isolation = False

    class Args(PluginABC.Args):
        origin: str
        destination: str
        files: list[str]

    def _run(self, args: Args, *, verbose: bool) -> None:
        import shutil

        shutil.copytree(args.source, args.destination)


class CopyTasksFilesPlugin(PluginABC):
    """Plugin for copying task files."""

    name = "copy_tasks_files"
    supports_isolation = False

    class Args(PluginABC.Args):
        origin: str
        destination: str
        tasks: list[str]
        files: list[str]

    def _run(self, args: Args, *, verbose: bool) -> None:
        import os
        import shutil

        for task_sub_path in args.tasks:
            task_path = os.path.join(args.origin, task_sub_path)
            shutil.copytree(task_path, args.destination)


class CheckRegexpPlugin(PluginABC):
    """Plugin for checking regexp."""

    name = "check_regexp"
    supports_isolation = False

    class Args(PluginABC.Args):
        origin: str
        regexps: list[str]

    def _run(self, args: Args, *, verbose: bool) -> None:
        import os
        import re

        for regexp in args.regexps:
            for root, dirs, files in os.walk(args.origin):
                for file in files:
                    if re.match(regexp, file):
                        raise Exception(f"File {file} matches regexp {regexp}")
