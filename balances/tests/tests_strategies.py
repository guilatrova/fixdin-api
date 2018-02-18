from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from django.test import TestCase
from unittest import skip
from unittest.mock import patch, MagicMock
from transactions.tests.base_test import BaseTestHelper
from transactions.models import Transaction
from balances.models import PeriodBalance
from balances.strategies import CREATED, UPDATED, BaseStrategy, CreateStrategy, CascadeStrategy
from balances.tests.helpers import PeriodBalanceWithTransactionsFactory

class StrategyTestHelper:
    def create_period_balance(self, start, end, account=None):
        PeriodBalance.objects.create(
            account=account or self.account,
            start_date=start,
            end_date=end,
            closed_effective_value=0,
            closed_real_value=0
        )

    def mock_transaction_instance(self, **kwargs):
        self.strategy.instance = MagicMock(account=self.account, **kwargs)

class BaseStrategyTestCase(TestCase, BaseTestHelper, StrategyTestHelper):
    
    @patch.multiple(BaseStrategy, __abstractmethods__=set()) #Allow instantiate abstract class
    def setUp(self):
        self.user = self.create_user('testuser', email='testuser@test.com', password='testing')[0]
        self.account = self.create_account()
        self.strategy = BaseStrategy(None, UPDATED)

    def test_get_due_lower_date(self):
        self.mock_transaction_instance(
            due_date=date(2014, 8, 22), 
            payment_date=date(2017, 1, 1)
        )

        self.assertEqual(self.strategy.get_lower_date(), self.strategy.instance.due_date)
    
    def test_get_payment_lower_date(self):
        self.mock_transaction_instance(
            due_date=date(2014, 8, 22), 
            payment_date=date(2010, 1, 1)
        )

        self.assertEqual(self.strategy.get_lower_date(), self.strategy.instance.payment_date)

    def test_get_lower_date_payment_none(self):
        self.mock_transaction_instance(
            due_date=date(2014, 8, 22), 
            payment_date=None
        )

        self.assertEqual(self.strategy.get_lower_date(), self.strategy.instance.due_date)

    def test_is_from_previous_period_returns_true(self):
        self.mock_transaction_instance(
            due_date=date(2018, 1, 22), 
            payment_date=None
        )    
        self.create_period_balance(date(2018, 1, 1), date(2018, 1, 31))

        self.assertTrue(self.strategy.is_from_previous_period())

    def test_is_from_previous_period_returns_false(self):
        self.mock_transaction_instance(
            due_date=date(2018, 2, 22), 
            payment_date=None
        )
        self.create_period_balance(date(2018, 1, 1), date(2018, 1, 31))

        self.assertFalse(self.strategy.is_from_previous_period())

    def test_is_from_previous_period_another_account_returns_false(self):
        another_account = self.create_account(name='another')
        self.create_period_balance(date(2018, 1, 1), date(2018, 1, 31), another_account)
        self.mock_transaction_instance(
            due_date=date(2018, 1, 22),
            payment_date=date(2018, 1, 22)
        )

        self.assertFalse(self.strategy.is_from_previous_period())

class CreateStrategyTestCase(TestCase, BaseTestHelper, StrategyTestHelper):
    def setUp(self):
        self.user = self.create_user(email='testuser@test.com', password='testing')[0]
        self.account = self.create_account()
        self.strategy = CreateStrategy(None, CREATED)
    
    @patch('balances.factories.create_period_balance_for', side_effect=None)
    def test_is_from_previous_period_checks_missing_period(self, ignore_mock):
        self.mock_transaction_instance()
        with patch.object(self.strategy, 'is_missing_period', return_value=True) as mock:
            self.assertTrue(self.strategy.is_from_previous_period())
            self.assertTrue(mock.called)

    def test_is_missing_period_returns_true(self):
        self.mock_transaction_instance(
            due_date=date(2017, 8, 22),
            payment_date=date(2017, 8, 22)
        )

        self.assertTrue(self.strategy.is_missing_period(self.account))

    def test_is_missing_period_returns_false_current_period(self):
        self.create_period_balance(date(2018, 1, 1), date(2018, 1, 31))
        self.mock_transaction_instance(
            due_date=date.today(),
            payment_date=date.today()
        )

        self.assertFalse(self.strategy.is_missing_period(self.account))

    def test_is_missing_period_another_account(self):
        another_account = self.create_account(name='another')
        self.create_period_balance(date(2018, 1, 1), date(2018, 1, 31), another_account)
        self.mock_transaction_instance(
            due_date=date(2018, 1, 22),
            payment_date=date(2018, 1, 22)
        )

        #only existent for another account
        self.assertTrue(self.strategy.is_missing_period(self.account))