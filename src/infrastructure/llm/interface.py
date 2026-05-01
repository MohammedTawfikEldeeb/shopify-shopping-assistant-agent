from abc import ABC, abstractmethod


class LLMInterface(ABC):

    @abstractmethod
    def connect(self):
        pass

    @abstractmethod
    def disconnect(self):
        pass

    @abstractmethod
    def chat(self, messages: list, **kwargs):
        pass

    @abstractmethod
    def with_structured_output(self, schema):
        pass
