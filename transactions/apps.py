from django.apps import AppConfig

class TransactionsConfig(AppConfig):
    name = 'transactions'

    def ready(self):
        from transactions.signals import periodic, balance