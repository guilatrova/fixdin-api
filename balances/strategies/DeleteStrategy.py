from .CascadeStrategy import CascadeStrategy

class DeleteStrategy(CascadeStrategy):
    """
    Exclusive strategy to be triggered when a transaction is deleted    
    """

    def update_current_balance(self, instance):
        account = instance.account

        account.current_effective_balance -= instance.value
        account.current_real_balance -= instance.real_value

        account.save()