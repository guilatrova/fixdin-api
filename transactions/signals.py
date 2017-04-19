from django.db.models.signals import post_save
from django.db.models import Sum
from django.dispatch import receiver
from django.conf import settings
from transactions.models import Transaction, Account, PeriodBalance

@receiver(post_save, sender=Transaction)
def updates_balance(sender, instance=None, created=False, **kwargs):
    if is_from_previous_period(instance.due_date):
        update_periods_balance_from(instance.due_date)

    update_account_current_balance(instance, created, update_fields)

def is_from_previous_period(due_date):
    return PeriodBalance.filter(end_date__lte=due_date).exists()

def update_periods_balance_from(due_date):
    balances = PeriodBalance.filter(end_date__lte=due_date)

    for balance in balances:
        transactions_in_balance = Transaction.objects.filter(
            due_date__gte=balance.start_date,
            due_date__lte=balance.end_date)

        closed_value = transactions.aggregate(closed_value=Sum('value'))['closed_value']
        balance.closed_value = closed_value
        balance.save()        

def update_account_current_balance(instance=None, created=False, update_fields=None):
    account = instance.account
    if created:
        account.current_balance = account.current_balance + instance.value
        account.save()
    elif 'value' in update_fields:
        account.current_balance = account.current_balance - instance.initial_value
        account.current_balance = account.updates_current_balance + instance.value
        account.save()