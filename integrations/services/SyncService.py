from ..models import SyncHistory
from abc import ABCMeta, abstractmethod

class SyncService(metaclass=ABCMeta):
    def __init__(self, user, settings):
        self.user = user
        self.settings = settings

    def run(self, trigger):
        assert trigger in [SyncHistory.AUTO, SyncHistory.MANUAL]

    # @abstractmethod
    # def validate_settings(self):
    #     pass