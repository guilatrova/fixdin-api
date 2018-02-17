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

@receiver(post_save, sender=Transaction)
def created_or_updated_transaction_updates_balance(sender, instance=None, created=False, **kwargs):
    if not created:
        action = UPDATED
        if instance.initial_value == instance.value:
            return
    else:
        action = CREATED

    trigger_updates(instance, action)

@receiver(post_delete, sender=Transaction)
def deleted_transaction_updates_balance(sender, instance=None, **kwargs):
    trigger_updates(instance, DELETED)

def trigger_updates(instance, action):
    strategy = DifferentialValueStrategy(instance, action)
    strategy.run()
    # if instance.payment_date:
    #     if is_missing_period(instance.payment_date):
    #         create_period_balance_for(instance)
    #     if is_from_previous_period(instance.payment_date):
    #         update_periods_balance_from(instance.payment_date)        

    # update_account_current_balance(instance, action)

def requires_updates(transaction):
    attrs = ['value', 'due_date', 'payment_date']
    for attr in attrs:
        if getattr(transaction, 'initial_' + attr) != getattr(transaction, attr):
            return True

    return False

def is_from_previous_period(payment_date):
    return PeriodBalance.objects.filter(end_date__gte=payment_date).exists()

def is_missing_period(date):
    cmp_date = date.date() if isinstance(date, datetime.datetime) else date
    cur_start, cur_end = get_current_period()
    start, end = get_period_from(date)

    if not PeriodBalance.objects.filter(start_date=start,end_date=end).exists() and cmp_date < cur_start:
        return True

    return False

def update_periods_balance_from(payment_date):
    balances = PeriodBalance.objects.filter(end_date__gte=payment_date).order_by('end_date')
    dif_to_cascade = 0

    for balance in balances:
        transactions_in_balance = balance.get_transactions()

        new_closed_effective_value = transactions_in_balance.aggregate(closed_effective_value=Sum('value'))['closed_effective_value']
        dif = new_closed_effective_value - balance.closed_effective_value

        balance.closed_effective_value = new_closed_effective_value + dif_to_cascade

        dif_to_cascade = dif_to_cascade + dif
        balance.save()        

def update_account_current_balance(instance, action):
    account = instance.account

    if action == DELETED:
        account.current_balance = account.current_balance - instance.value        
    elif action == CREATED:
        account.current_balance = account.current_balance + instance.value
    else:
        dif = instance.initial_value - instance.value
        account.current_balance = account.current_balance - dif

    account.save()