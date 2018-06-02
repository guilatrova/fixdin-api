from abc import ABCMeta, abstractmethod

from ..models import SyncHistory


class SyncService(metaclass=ABCMeta):
    def __init__(self, user, settings):
        self.user = user
        self.settings = settings

    def run(self, trigger):
        assert trigger in [SyncHistory.AUTO, SyncHistory.MANUAL]

    @abstractmethod
    def validate_settings(self):
        """
        Verifies if defined settings actually works. 
        It doesn't check coherence like: duplicates, type, etc.
        """
        pass
