import calendar
import datetime
from django.db.models.signals import post_save, post_delete
from django.db.models import Sum
from django.dispatch import receiver
from transactions.models import Transaction
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
    if instance.payment_date:
        # if is_missing_period(instance.payment_date):
        #     create_period_balance_for(instance)
        if is_from_previous_period(instance.payment_date):
            update_periods_balance_from(instance.payment_date)        

    update_account_current_balance(instance, action)

def requires_updates(transaction):
    attrs = ['value', 'due_date', 'payment_date']
    for attr in attrs:
        if getattr(transaction, 'initial_' + attr) != getattr(transaction, attr):
            return True

    return False

def is_from_previous_period(payment_date):
    return PeriodBalance.objects.filter(end_date__gte=payment_date).exists()

def is_missing_period(payment_date):
    cmp_date = payment_date.date() if isinstance(payment_date, datetime.datetime) else payment_date
    cur_start, cur_end = get_current_period()
    start, end = get_period_from(payment_date)

    if not PeriodBalance.objects.filter(start_date=start,end_date=end).exists() and cmp_date < cur_start:
        return True

    return False

def get_current_period():
    return get_period_from(datetime.date.today())

def get_period_from(datev):
    start = datev.replace(day=1)
    week, days_amount = calendar.monthrange(start.year, start.month)
    end = start.replace(day=days_amount)

    return (start, end)

def create_period_balance_for(transaction):
    start, end = get_period_from(transaction.payment_date)
    PeriodBalance.objects.create(
        account=transaction.account,
        start_date=start,
        end_date=end,
        closed_value=transaction.value #Since I'm creating specific for this transaction, I can start with value
    )

def update_periods_balance_from(payment_date):
    balances = PeriodBalance.objects.filter(end_date__gte=payment_date).order_by('end_date')
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