from datetime import date
from calendar import monthrange
from dateutil.relativedelta import relativedelta
from transactions.models import Transaction

def create_periodic_transactions(**kwargs):
    periodic = kwargs.pop('periodic')
    transactions_list = []

    increment_args = get_increment_args(periodic)

    start_date = kwargs.pop('due_date')
    current_due_date = start_date
    
    parent = None
    while current_due_date <= periodic['until']:
        trans = Transaction.objects.create(due_date=current_due_date, **kwargs)

        #Periodics should point to parent or itself
        if parent is None:
            parent = trans
            
            trans.periodic_transaction_id = trans.id
            kwargs['periodic_transaction_id'] = parent.id

            trans.save()

        transactions_list.append(trans)
        current_due_date = current_due_date + relativedelta(**increment_args)

        if need_to_fix_date(periodic['period'], start_date):
            current_due_date = fix_last_day_month(start_date, current_due_date)

    return transactions_list

def get_increment_args(periodic):
    distance = periodic['distance']
    choices = {
        'daily':   {'days': distance},
        'weekly':  {'weeks': distance},
        'monthly': {'months': distance},
        'yearly':  {'years': distance}
    }
    return choices.get(periodic['period'])

def need_to_fix_date(interval, start_date):
    if interval != 'daily' and interval != 'weekly':
        if start_date.day >= 29:
            return True

    return False

def fix_last_day_month(start_date, current_date):
    if current_date.day != start_date.day:
        week_count, last_day = monthrange(current_date.year, current_date.month)

        return date(current_date.year, current_date.month, last_day)
