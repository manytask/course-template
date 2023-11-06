from __future__ import annotations

from checker.plugins import PluginABC


class RunPytestPlugin(PluginABC):
    """Plugin for running pytest."""

    name = 'run_pytest'
    supports_isolation = True

    class Args(PluginABC.Args):
        origin: str
        args: list[str]
        timeout: int | None = None

    def _run(self, args: Args, *, verbose: bool) -> None:
        """Run the plugin."""
        import pytest
        pytest.main(
            args.args,
            args.origin,
        )
