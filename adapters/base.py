# adapters/base.py
from abc import ABC, abstractmethod

class BaseAdapter(ABC):
    def __init__(self, config):
        self.config = config

    @abstractmethod
    def run(self, data=None):
        pass