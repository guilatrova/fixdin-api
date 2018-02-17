import calendar
import datetime
from django.db.models.signals import post_save, post_delete
from django.db.models import Sum
from django.dispatch import receiver
from transactions.models import Transaction
from balances.models import PeriodBalance
from balances.factories import create_period_balance_for
from balances.services.periods import get_current_period, get_period_from
from balances.strategies.actions import CREATED, UPDATED, DELETED
from balances.strategies.DifferentialValueStrategy import DifferentialValueStrategy
from balances.strategies.CreateStrategy import CreateStrategy

@receiver(post_save, sender=Transaction)
def created_or_updated_transaction_updates_balance(sender, instance=None, created=False, **kwargs):
    if not created:
        action = UPDATED
        if not requires_updates(instance):
            return
    else:
        action = CREATED

    trigger_updates(instance, action)

@receiver(post_delete, sender=Transaction)
def deleted_transaction_updates_balance(sender, instance=None, **kwargs):
    trigger_updates(instance, DELETED)

def trigger_updates(instance, action):
    strategy_cls = CreateStrategy if action == CREATED else DifferentialValueStrategy
    strategy = strategy_cls(instance, action)
    strategy.run()

def requires_updates(transaction):
    attrs = ['value', 'due_date', 'payment_date']
    for attr in attrs:
        if getattr(transaction, 'initial_' + attr) != getattr(transaction, attr):
            return True

    return False