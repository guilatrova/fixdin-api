from abc import ABC, abstractmethod

from balances.models import PeriodBalance


class BaseStrategy(ABC):
    """
    Base strategy class that aims to be inherited by classes that
    handles calculation of previous PeriodBalances and current account balances.
    """
    def __init__(self, instance):
        """
        Initializes strategy class

        :param instance: Transaction which triggered recalculation
        """
        self.instance = instance        

    def get_lower_date(self):
        due_date = self.instance.due_date
        payment_date = self.instance.payment_date

        return due_date if not payment_date or due_date < payment_date else payment_date

    def get_periods_of(self, account):
        return PeriodBalance.objects.filter(account=account)

    def is_from_previous_period(self):
        lower_date = self.get_lower_date()

        'x means date, brackets periods: [...x..x..x][..x.....x."]"....'
        return self.get_periods_of(self.instance.account).filter(end_date__gte=lower_date).exists()

    @abstractmethod
    def update_previous_periods(self, account):
        pass

    @abstractmethod
    def update_current_balance(self):
        pass    

    def run(self):
        if self.is_from_previous_period():
            self.update_previous_periods(self.instance.account)

        self.update_current_balance(self.instance)
