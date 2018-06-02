from abc import ABC, abstractmethod


class BaseStrategy(ABC):
    """
    Base strategy class that aims to be inherited by classes that
    handles specific queries about balance
    """

    @abstractmethod
    def apply(self, query):
        pass
