from balances.models import PeriodBalance
from balances.services.periods import get_period_from
from balances.strategies.periods import (
    CREATED, 
    UPDATED, 
    DELETED, 
    CreateStrategy, 
    UpdateStrategy, 
    ChangedAccountStrategy, 
    DeleteStrategy
)

def create_period_strategy(action, transaction):
    if action == CREATED:
        return CreateStrategy(transaction)
        
    if action == DELETED:
        return DeleteStrategy(transaction)
        
    if action == UPDATED:
        if transaction.initial_account != transaction.account:
            return ChangedAccountStrategy(transaction)
        return UpdateStrategy(transaction)

def create_period_balance_for(transaction, dates):
    result = []
    for date in dates:
        period = get_period_from(date)
        result.append(_create_period_balance_for_period(transaction, period))

    return result

def _create_period_balance_for_period(transaction, period):
    start, end = period
    value = transaction.value if transaction.due_date >= start and transaction.due_date <= end else 0
    real_value = transaction.value if transaction.payment_date and transaction.payment_date >= start and transaction.payment_date <= end else 0

    return _create(transaction.account, start, end, value, real_value)

def _create(account, start, end, effective_value, real_value):
    return PeriodBalance.objects.create(
        account=account,
        start_date=start,
        end_date=end,
        closed_effective_value=effective_value,
        closed_real_value=real_value
    )