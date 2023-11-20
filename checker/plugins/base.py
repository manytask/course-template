from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, ValidationError

from checker.exceptions import BadConfig


class PluginABC(ABC):
    """Abstract base class for plugins."""

    name: str
    supports_isolation: bool = False

    class Args(BaseModel):
        pass

    def run(self, args: dict[str, Any], *, verbose: bool) -> None:
        """Run the plugin."""
        self._run(self.Args(**args), verbose=verbose)

    @classmethod
    def validate_args(cls, args: dict[str, Any]) -> None:
        """Validate the plugin arguments."""
        try:
            cls.Args(**args)
        except ValidationError as e:
            raise BadConfig(f"Plugin {cls.name} arguments validation error:\n{e}")

    @abstractmethod
    def _run(self, args: Args, *, verbose: bool) -> None:
        pass
