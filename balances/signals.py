import calendar
import datetime
from django.db.models.signals import post_save, post_delete
from django.db.models import Sum
from django.db import transaction as db_transaction
from django.dispatch import receiver
from transactions.models import Transaction
from balances.factories import create_strategy
from balances.services.periods import get_current_period, get_period_from
from balances.strategies import CREATED, UPDATED, DELETED

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

@db_transaction.atomic
def trigger_updates(instance, action):
    _fix_dates(instance)
    strategy = create_strategy(action, instance)
    strategy.run()

def requires_updates(transaction):
    attrs = ['value', 'due_date', 'payment_date']
    for attr in attrs:
        if getattr(transaction, 'initial_' + attr) != getattr(transaction, attr):
            return True

    return False

def _fix_dates(transaction):
    """
    Strip time of transaction dates.
    Sometimes because of tests some dates are in format "datetime" and others "date", which causes issues.
    """
    def _fix(attr):
        val = getattr(transaction, attr)
        if isinstance(val, datetime.datetime):
            setattr(transaction, attr, val.date())    

    _fix('due_date')
    _fix('payment_date')
