from __future__ import annotations

from pydantic import FilePath, DirectoryPath, validator, field_validator

from .base import PluginABC


class RunScriptPlugin(PluginABC):
    """Plugin for running scripts."""

    name = "run_script"
    supports_isolation = True

    class Args(PluginABC.Args):
        origin: str
        script: str | list[str]
        timeout: int | None = None

    def _run(self, args: Args, *, verbose: bool) -> None:
        """Run the plugin."""
        import subprocess

        subprocess.run(
            args.script,
            cwd=args.origin,
            timeout=args.timeout,
            check=True,
        )
