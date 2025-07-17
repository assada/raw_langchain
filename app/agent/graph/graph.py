from abc import ABC, abstractmethod

from app.agent.models import ModelConfig


class Graph(ABC):
    @abstractmethod
    def build_graph(self):
        pass

    def _get_model_config(self, name: str) -> ModelConfig:
        """Retrieve the model configuration."""
        # This method should be implemented to fetch the actual model configuration
        raise NotImplementedError("This method should be implemented in subclasses.")
