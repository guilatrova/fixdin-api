from .CreateStrategy import CreateStrategy

#We inherit from Create because it may be changed to an account without a PeriodBalance, so it will be created if needed
class ChangedAccountStrategy(CreateStrategy):
    """
    Exclusive strategy to be triggered when user changes any transaction
    from account A to B.
    e.g. User changed transaction gas from account 'wallet' to 'bank'.
    """

    def get_lower_date(self):
        def get_lower(x, y):
            if x and y:
                return x if x < y else y
            return x or y

        lower_payment = get_lower(self.instance.initial_payment_date, self.instance.payment_date)
        lower_due = get_lower(self.instance.initial_due_date, self.instance.due_date)
        return get_lower(lower_due, lower_payment)

    def run(self):
        if self.is_from_previous_period():
            self.update_previous_periods(self.instance.initial_account)
            self.update_previous_periods(self.instance.account)

        self.update_current_balance(self.instance, self.action)

    def update_current_balance(self, instance, action):
        self._update_balance_initial_account(instance, instance.initial_account)
        self._update_balance_new_account(instance, instance.account)

    def _update_balance_initial_account(self, instance, initial_account):
        #User may have changed values and dates too, so is import to consider initial values here
        real_value = instance.initial_value if instance.initial_payment_date else 0

        initial_account.current_effective_balance = initial_account.current_effective_balance - instance.initial_value
        initial_account.current_real_balance = initial_account.current_real_balance - real_value
        initial_account.save()

    def _update_balance_new_account(self, instance, new_account):
        real_value = instance.value if instance.payment_date else 0

        new_account.current_effective_balance = new_account.current_effective_balance + instance.value
        new_account.current_real_balance = new_account.current_real_balance + real_value
        new_account.save()
