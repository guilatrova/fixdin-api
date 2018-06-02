from django.apps import AppConfig


class BalancesConfig(AppConfig):
    name = 'balances'

    def ready(self):
        from balances import signals
