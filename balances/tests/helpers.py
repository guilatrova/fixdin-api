import calendar
from contextlib import contextmanager
from datetime import date, datetime

from dateutil.relativedelta import relativedelta
from django.db.models import signals

from balances.models import PeriodBalance
from balances.signals import created_or_updated_transaction_updates_balance, deleted_transaction_updates_balance
from transactions.models import Transaction


@contextmanager
def balance_signals_disabled():
    try:
        signals.post_save.disconnect(
            created_or_updated_transaction_updates_balance,
            sender=Transaction
        )
        signals.post_delete.disconnect(
            deleted_transaction_updates_balance,
            sender=Transaction,
        )
        yield
    finally:
        signals.post_save.connect(
            created_or_updated_transaction_updates_balance,
            sender=Transaction
        )
        signals.post_delete.connect(
            deleted_transaction_updates_balance,
            sender=Transaction,
        )


class PeriodBalanceWithTransactionsFactory:
    """
    Factory responsible for creating PeriodBalances and Transactions
    to match values and TO BE USED ONLY ON tests
    """
    #Default values
    START_DATE = date(year=2017, month=1, day=1)
    PERIODS = 4 #A PERIOD IS A MONTH
    TRANSACTIONS_PER_PERIOD = 50 #50*4 = 200
    START_VALUE = 1
    VALUE_INCREMENT_MULTIPLIER_PER_PERIOD = 10

    def __init__(self, category, account):
        self.category = category
        self.account = account

    def create(self):
        with balance_signals_disabled():
            self.create_transactions()
            self.create_period_balances()

    def create_transactions(self):
        transaction_value = self.START_VALUE
        total_value = 0

        for period in range(self.PERIODS):
            current_period = self.START_DATE + relativedelta(months=+period)
            days_count = calendar.monthrange(current_period.year, current_period.month)[1]

            transactions_per_day = self.TRANSACTIONS_PER_PERIOD / days_count
            add_remaning_transactions = False
            if self.TRANSACTIONS_PER_PERIOD % days_count != 0:
                add_remaning_transactions = True
                transactions_per_day = int(transactions_per_day)
            
            for day in range(1, days_count+1):
                current_date = date(year=current_period.year, month=current_period.month, day=day)
                total_value += self.create_multiple_transactions(transactions_per_day, current_date, transaction_value)

            if add_remaning_transactions:
                dif_to_create = self.TRANSACTIONS_PER_PERIOD - (transactions_per_day * days_count)
                last_day = date(year=current_period.year, month=current_period.month, day=days_count)
                total_value += self.create_multiple_transactions(dif_to_create, last_day, transaction_value)

            transaction_value = transaction_value * self.VALUE_INCREMENT_MULTIPLIER_PER_PERIOD

        self.account.current_effective_balance = total_value
        self.account.current_real_balance = total_value
        self.account.save()
    
    def create_period_balances(self):
        value = self.START_VALUE

        for period in range(self.PERIODS):
            start = self.START_DATE + relativedelta(months=+period)
            last_day = calendar.monthrange(start.year, start.month)[1]
            end = date(year=start.year, month=start.month, day=last_day)
            closed_effective_value = self.TRANSACTIONS_PER_PERIOD * value

            self.create_period_balance(start, end, closed_effective_value)

            value = value * self.VALUE_INCREMENT_MULTIPLIER_PER_PERIOD
    
    def create_multiple_transactions(self, how_many, date, value):
        for i in range(how_many):
            Transaction.objects.create(
                account=self.account, 
                due_date=date,
                payment_date=date,
                description='unit test',
                category=self.category,
                value=value,
                kind=Transaction.EXPENSE_KIND,
                details='')

        return value * how_many

    def create_period_balance(self, start, end, value):
        PeriodBalance.objects.create(
            account=self.account,
            start_date=start,
            end_date=end,
            closed_effective_value=value,
            closed_real_value=value
        )
