from typing import Any


class Task:

    def __init__(self, relative_path: str, name: str, parameters: dict[str, Any]):
        self.relative_path = relative_path
        self.name = name
        self.parameters = parameters

