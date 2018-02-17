import datetime
from balances.models import PeriodBalance
from balances.services.periods import get_current_period, get_period_from
from balances.factories import create_period_balance_for
from .DifferentialValueStrategy import DifferentialValueStrategy
from .actions import CREATED

class CreateStrategy(DifferentialValueStrategy):
    def __init__(self, instance, action):
        super().__init__(instance, action)
        assert action == CREATED, 'CreateStrategy only accepts create action'

    def is_missing_period(self):
        date = self.get_lower_date()
        cmp_date = date.date() if isinstance(date, datetime.datetime) else date
        cur_start, cur_end = get_current_period()
        start, end = get_period_from(date)

        return (cmp_date < cur_start and 
            not PeriodBalance.objects.filter(start_date=start,end_date=end).exists())

    def is_from_previous_period(self):
        if self.is_missing_period():
            create_period_balance_for(self.instance)
            return True
        
        return super().is_from_previous_period()
