from calendar import monthrange
from datetime import date

from dateutil.relativedelta import relativedelta

from transactions.models import BoundReasons, Transaction


def create_periodic_transactions(**kwargs):
    periodic = kwargs.pop('periodic')
    kwargs['bound_reason'] = BoundReasons.PERIODIC_TRANSACTION
    transactions_list = []

    increment_args = get_increment_args(periodic, periodic['interval'])

    start_date = kwargs.pop('due_date')
    current_due_date = start_date

    if 'how_many' in periodic:
        length = (periodic['how_many']-1) * periodic['interval']
        increment = get_increment_args(periodic, length)
        date_until = start_date + relativedelta(**increment)
    else:
        date_until = periodic['until']
    
    #Periodics should point to parent or itself
    parent = Transaction.objects.create(due_date=current_due_date, **kwargs)
    parent.bound_transaction_id = parent.id
    parent.save()
    if 'payment_date' in kwargs:
        kwargs.pop('payment_date') #payment date cant repeat
    kwargs['bound_transaction_id'] = parent.id
    transactions_list.append(parent)
    current_due_date = current_due_date + relativedelta(**increment_args)

    while current_due_date <= date_until:
        trans = Transaction.objects.create(due_date=current_due_date, **kwargs)
        transactions_list.append(trans)

        if need_to_fix_date(periodic['frequency'], start_date):
            current_due_date = fix_last_day_month(start_date, current_due_date)

        current_due_date = current_due_date + relativedelta(**increment_args)

    return transactions_list

def get_increment_args(periodic, length):    
    choices = {
        'daily':   {'days': length},
        'weekly':  {'weeks': length},
        'monthly': {'months': length},
        'yearly':  {'years': length}
    }
    return choices.get(periodic['frequency'])

def need_to_fix_date(interval, start_date):
    if interval != 'daily' and interval != 'weekly':
        if start_date.day >= 29:
            return True

    return False

def fix_last_day_month(start_date, current_date):
    if current_date.day != start_date.day:
        week_count, last_day = monthrange(current_date.year, current_date.month)

        return date(current_date.year, current_date.month, last_day)
