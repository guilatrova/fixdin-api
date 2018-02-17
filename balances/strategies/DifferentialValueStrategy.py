from django.db.models import Sum
from balances.models import PeriodBalance
from .BaseStrategy import BaseStrategy
from .actions import CREATED, DELETED, UPDATED

class DifferentialValueStrategy(BaseStrategy):
    """
    Strategy triggered to update values with no changes to dates.
    e.g. User changed value from R$ 10 to R$ 15.
    """

    def update_previous_periods(self):
        start_from = self.get_lower_date()

        balances = PeriodBalance.objects.filter(end_date__gte=start_from).order_by('end_date')
        dif_to_cascade = 0

        for balance in balances:
            transactions_in_balance = balance.get_transactions()

            new_closed_effective_value = transactions_in_balance\
                .aggregate(closed_effective_value=Sum('value'))['closed_effective_value']
            dif = new_closed_effective_value - balance.closed_effective_value

            balance.closed_effective_value = new_closed_effective_value + dif_to_cascade

            dif_to_cascade = dif_to_cascade + dif
            balance.save()        
        
    def update_current_balance(self, instance, action):
        account = instance.account

        if action == DELETED:
            account.current_balance = account.current_balance - instance.value        
        elif action == CREATED:
            account.current_balance = account.current_balance + instance.value
        else:
            dif = instance.initial_value - instance.value
            account.current_balance = account.current_balance - dif

        account.save()