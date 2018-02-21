from django.db.models import Q, Sum, Case, When, F
from django.db.models.functions import Coalesce
from transactions.models import Transaction
from balances.models import PeriodBalance
from balances.services import periods

#TODO: User / Account(s)
def calculate_account_current_balance(account_id):
    periods = PeriodBalance.objects.filter(account_id=account_id)
    real = sum(x.closed_real_value for x in periods)
    effective = sum(x.closed_effective_value for x in periods)

    open_balance = _calculate_open_balance(account_id)    

    return { 
        'real': real + open_balance['real'], 
        'effective': effective + open_balance['effective']
    }

def _calculate_open_balance(account_id):
    start, end = periods.get_current_period()

    #TODO: create manager for this date stuff:
    return Transaction.objects.\
        filter(account_id=account_id).\
        filter(
            Q(due_date__gte=start, due_date__lte=end) | 
            Q(payment_date__gte=start, payment_date__lte=end)
        ).\
        aggregate(
            effective=Coalesce(Sum('value'), 0),
            real=Coalesce(Sum(Case(When(payment_date__isnull=False, then=F('value')), default=0)), 0)
        )
    