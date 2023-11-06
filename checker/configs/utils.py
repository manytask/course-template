from pathlib import Path
import re
from typing import Any

import yaml
import pydantic

from ..exceptions import BadConfig


class CustomBaseModel(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(extra='forbid')


class YamlLoaderMixin:
    @classmethod
    def from_yaml(cls, path: Path) -> 'YamlLoaderMixin':
        try:
            with path.open() as f:
                return cls(**yaml.safe_load(f))
        except FileNotFoundError:
            raise BadConfig(f'File {path} not found')
        except yaml.YAMLError as e:
            raise BadConfig(f'Config YAML error:\n{e}')
        except pydantic.ValidationError as e:
            raise BadConfig(f'Config Validation error:\n{e}')

    def to_yaml(self, path: Path) -> None:
        with path.open('w') as f:
            yaml.dump(self.dict(), f)


class ParametersResolver:
    """
    A simple resolver that can handle expressions in the config files like ${{ some expression here }}.
    The following syntax is supported:
    0. you can use bool, null/None, int, float, str and flat list types
    1. context consists of parameters from the config file and environment variables

    """

    pattern = re.compile(r"\${{\s*(\w+)\s*}}", re.DOTALL)  # "some ${{ var }} string"
    full_pattern = re.compile(r"^\${{\s*(\w+)\s*}}$", re.DOTALL)  # "${{ var }}"

    def __init__(self, context: dict[str, Any]):
        self.context = context
        for value in self.context.values():
            if not isinstance(value, (bool, type(None), int, float, str, list)):
                raise BadConfig(f'Expression resolver does not support {type(value)} type of {value}')

    def _evaluate_single_expression(self, variable):
        """Evaluate a single variable from the context."""
        if variable in self.context:
            return self.context[variable]
        else:
            raise BadConfig(f"Variable '{variable}' not found in context")

    def resolve(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """
        Resolve the arguments.
        :param arguments: arguments with expressions to resolve,
                          some string with placeholders e.g. "Some ${{ var }} string"
        :return: resolved expression string, resolved if only expression found or original expression if no placeholders

        Examples (individual expressions), where var = 1, var2 = 2 ints:
        "Some ${{ var }} string" -> "Some 1 string"
        "Some ${{ var }} string ${{ var2 }}" -> "Some 1 string 2"
        "${{ var }}" -> 1 (int type)
        "${{ var }} " -> "1 " (cast to str type)
        """

        return {
            key: self.resolve_single(value)
            for key, value in arguments.items()
        }

    def resolve_single(self, expression: str) -> Any:
        # If the entire string is one placeholder, return its actual type
        full_match = self.full_pattern.fullmatch(expression)
        if full_match:
            return self._evaluate_single_expression(full_match.group(1))

        # If not, substitute and return the result as a string
        def substitute(match: re.Match) -> str:
            return str(self._evaluate_single_expression(match.group(1)))

        resolved_expression = self.pattern.sub(substitute, expression)
        return resolved_expression
