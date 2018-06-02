from .CreateStrategy import CreateStrategy


#We inherit from Create because it may be changed some date without a PeriodBalance, 
#so it will be created if needed
class UpdateStrategy(CreateStrategy):
    """
    Strategy to handle when something were changed (value or any date)
    e.g. User changed transaction value from R$ 10,00 to R$ 30,00
    """

    def get_lower_date(self):
        def get_lower(x, y):
            if x and y:
                return x if x < y else y
            return x or y

        lower_payment = get_lower(self.instance.initial_payment_date, self.instance.payment_date)
        lower_due = get_lower(self.instance.initial_due_date, self.instance.due_date)
        return get_lower(lower_due, lower_payment)

    def update_current_balance(self, instance, action=None):
        account = instance.account

        dif = instance.initial_value - instance.value
        real_dif = (instance.initial_value if instance.initial_payment_date else 0) - instance.real_value
        account.current_effective_balance -= dif #If is an income it will sum
        account.current_real_balance -= real_dif

        account.save()
