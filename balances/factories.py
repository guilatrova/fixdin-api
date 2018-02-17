import calendar
import datetime
from balances.models import PeriodBalance

def get_current_period():
    return get_period_from(datetime.date.today())

def get_period_from(date):
    start = date.replace(day=1)
    week, days_amount = calendar.monthrange(start.year, start.month)
    end = start.replace(day=days_amount)

    return (start, end)

def create_period_balance_for(transaction):
    start, end = get_period_from(transaction.due_date)
    real_value = transaction.value if transaction.payment_date else 0    

    PeriodBalance.objects.create(
        account=transaction.account,
        start_date=start,
        end_date=end,
        closed_effective_value=transaction.value, #Since I'm creating specific for this transaction, I can start with value
        closed_real_value=real_value
    )