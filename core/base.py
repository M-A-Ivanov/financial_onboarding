from abc import ABC, abstractmethod
from typing import Union, Dict, Any

from utils.paths import ExperimentPathManager


class BaseGenerator(ABC):
    client = None
    model_name: str = None

    def __init__(self, experiment_path_manager: ExperimentPathManager):
        self.path_manager = experiment_path_manager

    @abstractmethod
    def generate(self) -> str:
        pass

    @abstractmethod
    def save(self, output: Union[str, Dict[str, Any]]) -> str:
        pass

    @abstractmethod
    def get_prompt(self, *args) -> str:
        pass

    def create(self):
        return self.save(self.generate())

    @staticmethod
    def strip_markdown_code_block(md_string):
        lines = md_string.splitlines()
        # Filter out any line that starts with ```
        filtered = [line for line in lines if not line.strip().startswith("```")]
        return "\n".join(filtered)

