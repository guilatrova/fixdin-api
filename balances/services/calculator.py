from django.db.models import Case, F, Q, Sum, When
from django.db.models.functions import Coalesce

from balances.models import PeriodBalance
from balances.services import periods
from transactions.models import Transaction


class Calculator:
    def __init__(self, user_id, date_strategy, format_stategy):
        self.user_id = user_id
        self.date_strategy = date_strategy
        self.format_stategy = format_stategy

    def calculate(self, **filters):
        query = Transaction.objects.owned_by(self.user_id).filter(**filters)
        query = self.date_strategy.apply(query)
        return self.format_stategy.apply(query)

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

    return Transaction.objects.\
        filter(account_id=account_id).\
        in_date_range(start, end).\
        aggregate(
            effective=Coalesce(Sum('value'), 0), #TODO: quando cair num payment date não vai calcular um valor falso aqui? devo validar o due_date
            real=Coalesce(Sum(Case(When(payment_date__isnull=False, then=F('value')), default=0)), 0)
        )
