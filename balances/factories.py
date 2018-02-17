from balances.models import PeriodBalance
from balances.services.periods import get_period_from

def create_period_balance_for(transaction):
    due_period = get_period_from(transaction.due_date)
    payment_period = get_period_from(transaction.payment_date)

    if due_period == payment_period or payment_period is None:
        return _create_period_balance_for_period(transaction, due_period)
    else:
        return _create_period_balances_for_different_periods(transaction, due_period, payment_period)

def _create_period_balance_for_period(transaction, period):
    start, end = period
    real_value = transaction.value if transaction.payment_date else 0

    _create(transaction.account, start, end, transaction.value, real_value)

def _create_period_balances_for_different_periods(transaction, due_period, payment_period):
    due_start, due_end = due_period
    payment_start, payment_end = payment_period

    _create(transaction.account, due_start, due_end, transaction.value, 0)
    _create(transaction.account, payment_start, payment_end, 0, transaction.value)

def _create(account, start, end, effective_value, real_value):
    PeriodBalance.objects.create(
        account=account,
        start_date=start,
        end_date=end,
        closed_effective_value=effective_value,
        closed_real_value=real_value
    )