import datetime
from balances.services.periods import get_current_period, get_period_from
from balances import factories
from .CascadeStrategy import CascadeStrategy

class CreateStrategy(CascadeStrategy):
    """
    Exclusive strategy to be triggered when a new transaction is created.
    It creates a period if missing, cascade updating all PeriodBalances when needed and also current balance.
    """

    def check_missing_periods(self, account):
        missing_due = self._check_is_missing_period(account, self.instance.due_date)
        missing_payment = self._check_is_missing_period(account, self.instance.payment_date)

        if missing_due and missing_payment:
            return [self.instance.due_date, self.instance.payment_date]
        
        if missing_due:
            return [self.instance.due_date]

        if missing_payment:
            return [self.instance.payment_date]

        return False

    def _check_is_missing_period(self, account, date):
        if date is None:
            return False

        date = date.date() if isinstance(date, datetime.datetime) else date
        cur_start, cur_end = get_current_period()
        start, end = get_period_from(date)
        periods = self.get_periods_of(account)

        return (date < cur_start and 
            not periods.filter(start_date=start,end_date=end).exists())

    def is_from_previous_period(self):
        missing_periods = self.check_missing_periods(self.instance.account)
        if missing_periods:
            factories.create_period_balance_for(self.instance, missing_periods)
            return True
        
        return super().is_from_previous_period()

    def update_current_balance(self, instance):
        account = instance.account

        account.current_effective_balance += instance.value
        account.current_real_balance += instance.real_value

        account.save()