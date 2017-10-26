from ..models import SyncHistory

class SyncService:
    def __init__(self, settings):
        self.settings = settings

    def run(self, trigger):
        assert trigger in [SyncHistory.AUTO, SyncHistory.MANUAL]