import datetime
import calendar
from decimal import Decimal
from dateutil.relativedelta import relativedelta
from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from django.db import transaction
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework.authtoken.models import Token
from transactions.models import *

class BalanceTestCase(TestCase):
    '''
    TestCase created to test signals and reactions to PeriodBalance + Account.
    Any insert in Transaction which due date is in current period (aka month) should update Account.current_balance.
    Every other insert in past periods should cascade updating PeriodBalance until arrive current balance in Account.
    '''
    START_DATE = datetime.date(year=2017, month=1, day=1)
    PERIODS = 4 #A PERIOD IS A MONTH
    TRANSACTIONS_PER_PERIOD = 50 #50*4 = 200
    START_VALUE = 1
    VALUE_INCREMENT_MULTIPLIER_PER_PERIOD = 10
    PERIOD_BALANCES = [ 50, 500, 5000, 50000]
    SUM_PERIODS = 55550

    #Should be 4 CLOSED periods
    #Should update 2 period

    def setUp(self):        
        with transaction.atomic():
            self.user = self.create_user('testuser', email='testuser@test.com', password='testing')
            self.category = self.create_category('default category')        
            self.account = self.create_account()
            self.create_transactions()
            self.create_period_balances()

    def test_increase_transaction_from_first_period_assert_current_balance(self):
        old_value, new_value = self.update_first_transaction_from_period(100, 1)

        expected_balance = self.SUM_PERIODS - old_value + new_value

        self.assertEqual(Account.objects.first().current_balance, expected_balance)

    def test_decrease_transaction_from_second_period_assert_current_balance(self):
        old_value, new_value = self.update_first_transaction_from_period(1, 2)

        expected_balance = self.SUM_PERIODS - old_value + new_value

        self.assertEqual(Account.objects.first().current_balance, expected_balance)

    def test_increase_transaction_from_second_period_assert_next_periods(self):
        old_value, new_value = self.update_first_transaction_from_period(1000, 2)
        expected_balances = [ 50, 1400, 6400, 50900 ]

        balances = PeriodBalance.objects.all()
        for i in range(len(self.PERIOD_BALANCES)):
            self.assertEqual(balances[i].closed_value, expected_balances[i])

    def update_first_transaction_from_period(self, new_value, period):
        date = self.START_DATE + relativedelta(months=+period-1)

        transaction = Transaction.objects.filter(due_date=date).first()
        transaction.value = new_value
        transaction.save()

        return transaction.initial_value, new_value
    
    def create_transactions(self):
        transaction_value = self.START_VALUE

        for period in range(self.PERIODS):
            current_period = self.START_DATE + relativedelta(months=+period)
            days_count = calendar.monthrange(current_period.year, current_period.month)[1]

            transactions_per_day = self.TRANSACTIONS_PER_PERIOD / days_count
            add_remaning_transactions = False
            if self.TRANSACTIONS_PER_PERIOD % days_count != 0:
                add_remaning_transactions = True
                transactions_per_day = int(transactions_per_day)
            
            for day in range(1, days_count+1):
                current_date = datetime.date(year=current_period.year, month=current_period.month, day=day)
                self.create_transaction(transactions_per_day, current_date, transaction_value)

            if add_remaning_transactions:
                dif_to_create = self.TRANSACTIONS_PER_PERIOD - (transactions_per_day * days_count)
                last_day = datetime.date(year=current_period.year, month=current_period.month, day=days_count)
                self.create_transaction(dif_to_create, last_day, transaction_value)
            
            transaction_value = transaction_value * self.VALUE_INCREMENT_MULTIPLIER_PER_PERIOD

    def create_period_balances(self):
        value = self.START_VALUE

        for period in range(self.PERIODS):
            start = self.START_DATE + relativedelta(months=+period)
            last_day = calendar.monthrange(start.year, start.month)[1]
            end = datetime.date(year=start.year, month=start.month, day=last_day)
            closed_value = self.TRANSACTIONS_PER_PERIOD * value

            self.create_period_balance(start, end, closed_value)

            value = value * self.VALUE_INCREMENT_MULTIPLIER_PER_PERIOD
    
    def create_transaction(self, how_many, due_date, value):
        for i in range(how_many):
            Transaction.objects.create(
                account=self.account, 
                due_date=due_date,
                description='unit test',
                category=self.category,
                value=value,
                payed=True,
                details='')

    def create_period_balance(self, start, end, value):
        PeriodBalance.objects.create(
            account=self.account,
            start_date=start,
            end_date=end,
            closed_value=value
        )

    def create_account(self):
        account = Account.objects.create(name='default account', user=self.user, current_balance=0)
        return account

    def create_user(self, name='testuser', **kwargs):
        user = User.objects.create_user(kwargs)     

        return user

    def create_category(self, name, user=None, kind=Category.EXPENSE_KIND):
        if user is None:
            user = self.user

        category = Category.objects.create(kind=kind, user=user, name=name)
        return category