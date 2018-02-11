import calendar
from contextlib import contextmanager
from unittest import skip
from unittest.mock import patch
from datetime import date, datetime
from decimal import Decimal
from dateutil.relativedelta import relativedelta
from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from django.db import transaction as db_transaction
from django.db.models import signals
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework.authtoken.models import Token
from transactions.models import *
from transactions.tests.base_test import BaseTestHelper
from balances.models import PeriodBalance
from balances.signals import created_or_updated_transaction_updates_balance, deleted_transaction_updates_balance

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

class ApiTestCase(TestCase, BaseTestHelper):

    def setUp(self):
        self.user, token = self.create_user('testuser', email='testuser@test.com', password='testing')

        self.client = self.create_authenticated_client(token)
        self.account = self.create_account(self.user)
        self.category = self.create_category('category')

    def test_get_current_balance(self):
        '''
        Get current balance regardless of payed or not, until present date
        '''
        self.create_transaction(10)
        self.create_transaction(10)
        self.create_transaction(30)
        self.create_transaction(60)
        #tomorrow
        tomorrow = datetime.today() + relativedelta(days=1)
        self.create_transaction(100, due_date=tomorrow)

        response = self.client.get(reverse('balances'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['balance'], 110)

    def test_get_current_real_balance(self):
        '''
        Calculates balance based only in payed transactions
        '''
        self.create_transaction(30, payment_date=datetime.today())
        self.create_transaction(60, payment_date=datetime.today())
        #not payed
        self.create_transaction(10)
        self.create_transaction(10)

        url = reverse('balances') + '?payed=1'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['balance'], 90)

    def test_get_expected_balance_until_date(self):
        self.create_transaction(30, due_date=datetime(2017, 9, 1), payment_date=datetime.today())
        self.create_transaction(60, due_date=datetime(2017, 9, 4), payment_date=datetime.today())
        self.create_transaction(10, due_date=datetime(2017, 9, 15))
        self.create_transaction(25, due_date=datetime(2017, 9, 30))

        url = reverse('balances') + '?until=2017-09-30'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['balance'], 125)

class SignalsTestCase(TestCase, BaseTestHelper):
    '''
    TestCase created to test signals and reactions to PeriodBalance + Account.
    Any insert in Transaction which due date is in current period (aka month) should update Account.current_balance.
    Every other insert in past periods should cascade updating PeriodBalance until arrive current balance in Account.
    '''
    START_DATE = date(year=2017, month=1, day=1)
    PERIODS = 4 #A PERIOD IS A MONTH
    TRANSACTIONS_PER_PERIOD = 50 #50*4 = 200
    START_VALUE = 1
    VALUE_INCREMENT_MULTIPLIER_PER_PERIOD = 10
    PERIOD_BALANCES = [ 50, 500, 5000, 50000 ]
    SUM_PERIODS = 55550
    
    def setUp(self):        
        with db_transaction.atomic(), balance_signals_disabled():
            self.user = self.create_user('testuser', email='testuser@test.com', password='testing')[0]
            self.category = self.create_category('default category')        
            self.account = self.create_account()
            self.create_transactions()
            self.create_period_balances()

    def test_increase_transaction_value_from_first_period_assert_current_balance(self):
        old_value, new_value = self.update_first_transaction_from_period(100, 1)

        expected_balance = self.SUM_PERIODS - old_value + new_value

        self.assert_account_balance(expected_balance)

    def test_decrease_transaction_value_from_second_period_assert_current_balance(self):
        old_value, new_value = self.update_first_transaction_from_period(1, 2)

        expected_balance = self.SUM_PERIODS - old_value + new_value

        self.assert_account_balance(expected_balance)

    def test_increase_transaction_value_from_second_period_assert_next_periods(self):
        self.update_first_transaction_from_period(1000, 2)
        expected_balances = [ 50, 1490, 5990, 50990 ]

        self.assert_balances(expected_balances)

    def test_decrease_transaction_value_from_second_period_assert_next_periods(self):
        self.update_first_transaction_from_period(1, 2)
        expected_balances = [ 50, 491, 4991, 49991]

        self.assert_balances(expected_balances)

    def test_delete_from_first_period_assert_current_balance(self):
        transaction = Transaction.objects.all().first()
        transaction.delete()

        expected_balance = self.SUM_PERIODS - transaction.value

        self.assert_account_balance(expected_balance)

    def test_delete_from_first_period_assert_next_periods(self):
        transaction = Transaction.objects.all().first()
        transaction.delete()
        expected_balances = [ 49, 499, 4999, 49999]

        self.assert_balances(expected_balances)

    @patch('balances.signals.trigger_updates')
    def test_updated_transaction_with_no_changes_to_value_should_not_trigger_updates(self, mock):
        transaction = Transaction.objects.all().first()
        transaction.description = 'changed only description...'
        transaction.save()

        self.assertFalse(mock.called)

    def test_creates_period_when_non_existing(self):
        expected_start = date(2014, 8, 1)
        expected_end = date(2014, 8, 31)
        transaction = self.create_transaction(
            value=100,
            due_date=date(2014, 8, 22), 
            payment_date=date(2014, 8, 22)
        )

        self.assertTrue(
            PeriodBalance.objects.filter(start_date=expected_start, end_date=expected_end).exists())
        
    def assert_balances(self, expected_balances):
        balances = PeriodBalance.objects.all()
        for i in range(len(self.PERIOD_BALANCES)):
            self.assertEqual(balances[i].closed_value, expected_balances[i])

    def assert_account_balance(self, expected):
        account = Account.objects.get(pk=self.account.id)
        self.assertEqual(account.current_balance, expected)

    def update_first_transaction_from_period(self, new_value, period):
        date = self.START_DATE + relativedelta(months=+period-1)

        transaction = Transaction.objects.filter(due_date=date).first()
        transaction.value = new_value
        transaction.save()

        return transaction.initial_value, new_value
    
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

        self.account.current_balance = total_value
        self.account.save()

    def create_period_balances(self):
        value = self.START_VALUE

        for period in range(self.PERIODS):
            start = self.START_DATE + relativedelta(months=+period)
            last_day = calendar.monthrange(start.year, start.month)[1]
            end = date(year=start.year, month=start.month, day=last_day)
            closed_value = self.TRANSACTIONS_PER_PERIOD * value

            self.create_period_balance(start, end, closed_value)

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
            closed_value=value
        )