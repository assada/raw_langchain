from abc import ABC, abstractmethod


class Graph(ABC):
    @abstractmethod
    def build_graph(self):
        pass
