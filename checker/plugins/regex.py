from pydantic import DirectoryPath

from .base import PluginABC


class CheckRegexpsPlugin(PluginABC):
    """Plugin for checking forbidden regexps in a files."""

    name = "check_regexps"
    supports_isolation = False

    class Args(PluginABC.Args):
        origin: str
        regexps: list[str]

    def _run(self, args: Args, *, verbose: bool) -> None:
        import re
        from pathlib import Path

        for file in Path(args.origin).glob("**/*"):
            if file.is_file():
                with file.open() as f:
                    file_content = f.read()

                for regexp in args.regexps:
                    if re.search(regexp, file_content, re.MULTILINE):
                        raise Exception(f"File {file} matches regexp {regexp}")
