from  balances.models import PeriodBalance

#TODO: User / Account(s)
def calculate_account_current_real_balance(account_id):
    periods = PeriodBalance.objects.filter(account_id=account_id)
    return sum(x.closed_real_value for x in periods)
    