from balances.models import PeriodBalance
from balances.services.periods import get_period_from

def create_period_balance_for(transaction, dates):
    result = []
    for date in dates:
        period = get_period_from(date)
        result.append(_create_period_balance_for_period(transaction, period))

    return result

def _create_period_balance_for_period(transaction, period):
    start, end = period
    return _create(transaction.account, start, end, transaction.value, transaction.real_value)

def _create(account, start, end, effective_value, real_value):
    return PeriodBalance.objects.create(
        account=account,
        start_date=start,
        end_date=end,
        closed_effective_value=effective_value,
        closed_real_value=real_value
    )