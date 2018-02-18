from django.db.models import Sum, Case, When, F
from django.db.models.functions import Coalesce
from balances.models import PeriodBalance
from .BaseStrategy import BaseStrategy
from .actions import CREATED, DELETED, UPDATED

class CascadeStrategy(BaseStrategy):
    """
    Strategy triggered to update values with no changes to any dates.
    e.g. User changed value from R$ 10 to R$ 15.
    """

    def update_previous_periods(self, account):
        start_from = self.get_lower_date()

        balances = self.get_periods_of(account).filter(end_date__gte=start_from).order_by('end_date')
        dif_to_cascade = { 'effective': 0, 'real': 0 }

        for balance in balances:
            transactions_in_balance = balance.get_transactions()

            new_values = transactions_in_balance.aggregate(
                closed_effective_value=Coalesce(Sum('value'), 0),
                closed_real_value=Coalesce(Sum(Case(When(payment_date__isnull=False, then=F('value')), default=0)), 0)
            )

            dif = {
                'effective': new_values['closed_effective_value'] - balance.closed_effective_value,
                'real': new_values['closed_real_value'] - balance.closed_real_value
            }
            
            balance.closed_effective_value = new_values['closed_effective_value'] + dif_to_cascade['effective']
            balance.closed_real_value = new_values['closed_real_value'] + dif_to_cascade['real']

            dif_to_cascade['effective'] += dif['effective']
            dif_to_cascade['real'] += dif['real']

            balance.save()
        
    def update_current_balance(self, instance, action):
        account = instance.account
        real_value = instance.value if instance.payment_date else 0

        if action == DELETED:
            account.current_effective_balance -= instance.value
            account.current_real_balance -= real_value
        elif action == CREATED:
            account.current_effective_balance += instance.value
            account.current_real_balance += real_value
        else:
            dif = instance.initial_value - instance.value
            real_dif = (instance.initial_value if instance.initial_payment_date else 0) - real_value
            account.current_effective_balance -= dif #If is an income it will sum
            account.current_real_balance -= real_dif

        account.save()