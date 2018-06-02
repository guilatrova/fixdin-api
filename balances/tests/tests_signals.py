from datetime import date
from unittest import skip
from unittest.mock import patch

from dateutil.relativedelta import relativedelta
from django.test import TestCase

from balances.factories import create_period_balance_for
from balances.models import PeriodBalance
from balances.signals import requires_updates
from balances.tests.helpers import PeriodBalanceWithTransactionsFactory, balance_signals_disabled
from transactions.models import Account, Transaction
from transactions.tests.base_test import BaseTestHelper


class SignalsTestCase(TestCase, BaseTestHelper):
    def setUp(self):
        self.user = self.create_user('testuser', email='testuser@test.com', password='testing')[0]
        self.category = self.create_category('default category')
        self.account = self.create_account()

    def test_requires_updates_should_returns_true_when_value_changed(self):
        transaction = self.create_transaction(100)
        transaction.value = 200

        self.assertTrue(requires_updates(transaction))

    def test_requires_updates_should_returns_true_when_due_date_changed(self):
        transaction = self.create_transaction(100)
        transaction.due_date = date(2017, 1, 1)

        self.assertTrue(requires_updates(transaction))

    def test_requires_updates_should_returns_true_when_payment_date_changed(self):
        transaction = self.create_transaction(100)
        transaction.payment_date = date(2017, 1, 1)

        self.assertTrue(requires_updates(transaction))

    def test_requires_updates_should_returns_false_when_those_are_unchanged(self):
        """ 'those' means that any property that isn't 'value', 'due_date' or 'payment_date'. """
        transaction = self.create_transaction(100)
        transaction.description = 'changed'

        self.assertFalse(requires_updates(transaction))    

class SignalsIntegrationTestCase(TestCase, BaseTestHelper):
    '''
    TestCase created to test signals and reactions to PeriodBalance + Account.
    Any insert in Transaction which due date is in current period (aka month) should update Account balance.
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
        self.user = self.create_user('testuser', email='testuser@test.com', password='testing')[0]
        self.category = self.create_category('default category')        
        self.account = self.create_account()
        PeriodBalanceWithTransactionsFactory(self.category, self.account).create()

    def test_increase_transaction_value_from_first_period_assert_current_balance(self):
        old_value, new_value = self.update_first_transaction_from_period(100, 1)

        expected_balance = self.SUM_PERIODS - old_value + new_value

        self.assert_account_balance(expected_balance, expected_balance)

    def test_decrease_transaction_value_from_second_period_assert_current_balance(self):
        old_value, new_value = self.update_first_transaction_from_period(1, 2)

        expected_balance = self.SUM_PERIODS - old_value + new_value

        self.assert_account_balance(expected_balance, expected_balance)

    def test_increase_transaction_value_from_second_period_assert_next_periods(self):
        self.update_first_transaction_from_period(1000, 2)
        expected_balances = [ 50, 1490, 5990, 50990 ]

        self.assert_balances(expected_balances, expected_balances)

    def test_decrease_transaction_value_from_second_period_assert_next_periods(self):
        self.update_first_transaction_from_period(1, 2)
        expected_balances = [ 50, 491, 4991, 49991]

        self.assert_balances(expected_balances, expected_balances)

    def test_delete_from_first_period_assert_current_balance(self):
        transaction = Transaction.objects.all().first()
        transaction.delete()

        expected_balance = self.SUM_PERIODS - transaction.value

        self.assert_account_balance(expected_balance, expected_balance)

    def test_delete_from_first_period_assert_next_periods(self):
        transaction = Transaction.objects.all().first()
        transaction.delete()
        expected_balances = [ 49, 499, 4999, 49999]

        self.assert_balances(expected_balances, expected_balances)

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

    def assert_balances(self, effective_balances, real_values):
        balances = PeriodBalance.objects.all()
        for i in range(len(self.PERIOD_BALANCES)):
            self.assertEqual(balances[i].closed_effective_value, effective_balances[i])
            self.assertEqual(balances[i].closed_real_value, real_values[i])

    def assert_account_balance(self, effective_expected, real_expected):
        account = Account.objects.get(pk=self.account.id)
        self.assertEqual(account.current_effective_balance, effective_expected)
        self.assertEqual(account.current_real_balance, real_expected)

    def update_first_transaction_from_period(self, new_value, period):
        date = self.START_DATE + relativedelta(months=+period-1)

        transaction = Transaction.objects.filter(due_date=date).first()
        transaction.value = new_value
        transaction.save()

        return transaction.initial_value, new_value

    #TODO: TEST UPDATING BOTH DATES TO A UNEXISTENT PAST PERIOD
    #TODO: TEST UPDATING BOTH DATES TO A UNEXISTENT PAST DIFFERENT PERIODS
    #TODO: TEST UPDATING ONE DATE TO UNEXISTENT PAST PERIOD WHILE PRESERVING ANOTHER PERIOD    
    #TODO: CREATE TRANSACTION TO FUTURE DATE
    #TODO: SETUP PAYMENT TO FUTURE DATE
    #TODO: PAYED PAST DATE
    #TODO: DUEDATE AND PAYMENTDATE DIFFERENT PERIODS
