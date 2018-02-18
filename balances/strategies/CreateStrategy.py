import datetime
from balances.services.periods import get_current_period, get_period_from
from balances import factories
from .CascadeStrategy import CascadeStrategy
from .actions import CREATED

class CreateStrategy(CascadeStrategy):
    """
    Exclusive strategy to be triggered when a new transaction is created.
    It creates a period if missing, cascade updating all PeriodBalances when needed and also current balance.
    """

    def is_missing_period(self, account):
        date = self.get_lower_date()
        cmp_date = date.date() if isinstance(date, datetime.datetime) else date
        cur_start, cur_end = get_current_period()
        start, end = get_period_from(date)
        periods = self.get_periods_of(account)

        return (cmp_date < cur_start and 
            not periods.filter(start_date=start,end_date=end).exists())

    def is_from_previous_period(self):
        if self.is_missing_period(self.instance.account):
            factories.create_period_balance_for(self.instance)
            return True
        
        return super().is_from_previous_period()

    def update_current_balance(self, instance, action):
        account = instance.account
        real_value = instance.value if instance.payment_date else 0

        account.current_effective_balance += instance.value
        account.current_real_balance += real_value

        account.save()