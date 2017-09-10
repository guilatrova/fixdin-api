from django.db.models.signals import post_save, post_delete
from django.db.models import Sum
from django.dispatch import receiver
from django.conf import settings
from transactions.models import Transaction, Account
from balances.models import PeriodBalance

DELETED = 0
CREATED = 1
UPDATED = 2

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
    if is_from_previous_period(instance.due_date):
        update_periods_balance_from(instance.due_date)

    update_account_current_balance(instance, action)

def is_from_previous_period(due_date):
    return PeriodBalance.objects.filter(end_date__gte=due_date).exists()

def update_periods_balance_from(due_date):
    balances = PeriodBalance.objects.filter(end_date__gte=due_date).order_by('end_date')
    dif_to_cascade = 0

    for balance in balances:
        transactions_in_balance = balance.get_transactions()

        new_closed_value = transactions_in_balance.aggregate(closed_value=Sum('value'))['closed_value']
        dif = new_closed_value - balance.closed_value

        balance.closed_value = new_closed_value + dif_to_cascade

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