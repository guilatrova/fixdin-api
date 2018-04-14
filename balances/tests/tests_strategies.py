from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from django.test import TestCase
from unittest import skip
from unittest.mock import patch, MagicMock
from transactions.tests.base_test import BaseTestHelper
from transactions.models import Transaction, Account
from balances.models import PeriodBalance
from balances.tests.helpers import PeriodBalanceWithTransactionsFactory
from balances.strategies.periods import (
    BaseStrategy,
    CreateStrategy,
    ChangedAccountStrategy, 
    UpdateStrategy, 
    DeleteStrategy
)

class StrategyTestMixin:
    def setUp(self):
        self.user = self.create_user(email='testuser@test.com', password='testing')[0]
        self.account = self.create_account(current_effective_balance=100, current_real_balance=100)
        self.strategy = self.strategy_cls(None)

    def create_period_balance(self, start, end, account=None):
        PeriodBalance.objects.create(
            account=account or self.account,
            start_date=start,
            end_date=end,
            closed_effective_value=0,
            closed_real_value=0
        )

    def mock_transaction_instance(self, **kwargs):
        if 'value' in kwargs:
            kwargs.update({ 'real_value': kwargs['value'] if kwargs['payment_date'] else 0 })
        self.strategy.instance = MagicMock(account=self.account, **kwargs)

    def assert_account_balances(self, effective, real):
        account = Account.objects.get(pk=self.account.id)
        self.assertEqual(effective, account.current_effective_balance)
        self.assertEqual(real, account.current_real_balance)

class BaseStrategyTestCase(StrategyTestMixin, TestCase, BaseTestHelper):
    strategy_cls = BaseStrategy

    @patch.multiple(BaseStrategy, __abstractmethods__=set()) #Allow instantiate abstract class
    def setUp(self):
        super().setUp()

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

class CreateStrategyTestCase(StrategyTestMixin, TestCase, BaseTestHelper):
    strategy_cls = CreateStrategy
    
    @patch('balances.factories.create_period_balance_for', side_effect=None)
    def test_is_from_previous_period_checks_missing_period(self, ignore_mock):
        self.mock_transaction_instance()
        with patch.object(self.strategy, 'check_missing_periods', return_value=True) as mock:
            self.assertTrue(self.strategy.is_from_previous_period())
            self.assertTrue(mock.called)

    def test_check_missing_periods_returns_both_dates(self):
        self.mock_transaction_instance(
            due_date=date(2017, 8, 22),
            payment_date=date(2017, 8, 23)
        )
        expected = [date(2017, 8, 22), date(2017, 8, 23)]

        self.assertEqual(expected, 
            self.strategy.check_missing_periods(self.account))

    def test_check_missing_periods_returns_false_current_period(self):
        self.create_period_balance(date(2018, 1, 1), date(2018, 1, 31))
        self.mock_transaction_instance(
            due_date=date.today(),
            payment_date=date.today()
        )

        self.assertFalse(self.strategy.check_missing_periods(self.account))

    def test_check_missing_periods_another_account(self):
        another_account = self.create_account(name='another')
        self.create_period_balance(date(2018, 1, 1), date(2018, 1, 31), another_account)
        self.mock_transaction_instance(
            due_date=date(2018, 1, 22),
            payment_date=date(2018, 1, 22)
        )

        #only existent for another account
        self.assertTrue(self.strategy.check_missing_periods(self.account))

    def test_update_current_balance(self):
        self.mock_transaction_instance(
            due_date=date.today(),
            payment_date=date.today(),
            value=100
        )
        self.strategy.update_current_balance(self.strategy.instance)
        self.assert_account_balances(200, 200)

    def test_update_current_balance_without_payment_date(self):
        self.mock_transaction_instance(
            due_date=date.today(),
            payment_date=None,
            value=100
        )
        self.strategy.update_current_balance(self.strategy.instance)
        self.assert_account_balances(200, 100)    

class UpdateStrategyTestCase(StrategyTestMixin, TestCase, BaseTestHelper):
    strategy_cls = UpdateStrategy

    def setUp(self):
        super().setUp()
        self.another_account = self.create_account(name='other', current_effective_balance=100, current_real_balance=100)

    def test_get_lower_date_compare_old_dates(self):
        self.mock_transaction_instance(
            initial_due_date=date(2017, 1, 1),
            initial_payment_date=date(2016, 5, 1),
            due_date=date(2016, 12, 1),
            payment_date=date(2016, 12, 1)
        )

        self.assertEqual(self.strategy.get_lower_date(), self.strategy.instance.initial_payment_date)

    def test_get_lower_date_compare_none_dates(self):
        self.mock_transaction_instance(
            initial_due_date=date(2016, 5, 1),
            initial_payment_date=date(2017, 1, 1),
            due_date=date(2016, 12, 1),
            payment_date=None
        )

        self.assertEqual(self.strategy.get_lower_date(), self.strategy.instance.initial_due_date)

    def test_update_current_balance_increasing(self):
        self.mock_transaction_instance(
            initial_due_date=date(2017, 1, 1),
            initial_payment_date=date(2017, 1, 1),
            initial_value=100,
            due_date=date(2017, 1, 1),
            payment_date=date(2017, 1, 1),
            value=150
        )
        self.strategy.update_current_balance(self.strategy.instance)
        self.assert_account_balances(150, 150)

    def test_update_current_balance_remove_payment(self):
        self.mock_transaction_instance(
            initial_due_date=date(2017, 1, 1),
            initial_payment_date=date(2017, 1, 1),
            initial_value=100,
            due_date=date(2017, 1, 1),
            payment_date=None,
            value=100
        )
        self.strategy.update_current_balance(self.strategy.instance)
        self.assert_account_balances(100, 0)

    def test_update_current_balance_decreasing(self):
        self.mock_transaction_instance(
            initial_due_date=date(2017, 1, 1),
            initial_payment_date=date(2017, 1, 1),
            initial_value=100,
            due_date=date(2017, 1, 1),
            payment_date=date(2017, 1, 1),
            value=80
        )
        self.strategy.update_current_balance(self.strategy.instance)
        self.assert_account_balances(80, 80)

    def test_changed_due_date_to_past(self):
        self.mock_transaction_instance(
            initial_due_date=date(2017, 1, 1),
            initial_payment_date=date(2017, 1, 1),
            initial_value=100,
            due_date=date(2016, 12, 1), #PAST
            payment_date=date(2017, 1, 1),
            value=100
        )

class DeleteStrategyTestCase(StrategyTestMixin, TestCase, BaseTestHelper):
    strategy_cls = DeleteStrategy

    def test_update_current_balance(self):
        self.mock_transaction_instance(
            due_date=date(2017, 1, 1),
            payment_date=date(2017, 1, 1),
            value=50
        )

        self.strategy.update_current_balance(self.strategy.instance)
        self.assert_account_balances(50, 50)