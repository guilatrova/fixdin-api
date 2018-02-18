from .UpdateStrategy import UpdateStrategy

class ChangedAccountStrategy(UpdateStrategy):
    """
    Exclusive strategy to be triggered when user changes any transaction
    from account A to B.
    e.g. User changed transaction gas from account 'wallet' to 'bank'.
    """

    def run(self):
        if self.is_from_previous_period():
            self.update_previous_periods(self.instance.initial_account)
            self.update_previous_periods(self.instance.account)

        self.update_current_balance(self.instance)

    def update_current_balance(self, instance):
        self._update_balance_initial_account(instance, instance.initial_account)
        self._update_balance_new_account(instance, instance.account)

    def _update_balance_initial_account(self, instance, initial_account):
        #User may have changed values and dates too, so is import to consider initial values here
        initial_real_value = instance.initial_value if instance.initial_payment_date else 0

        initial_account.current_effective_balance = initial_account.current_effective_balance - instance.initial_value
        initial_account.current_real_balance = initial_account.current_real_balance - initial_real_value
        initial_account.save()

    def _update_balance_new_account(self, instance, new_account):
        new_account.current_effective_balance = new_account.current_effective_balance + instance.value
        new_account.current_real_balance = new_account.current_real_balance + instance.real_value
        new_account.save()
