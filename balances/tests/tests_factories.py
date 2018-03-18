from datetime import date
from dateutil.relativedelta import relativedelta
from django.test import TestCase
from unittest import skip
from unittest.mock import patch
from transactions.tests.base_test import BaseTestHelper
from transactions.models import Transaction, Account
from balances.models import PeriodBalance
from balances.signals import requires_updates
from balances.factories import create_period_balance_for
from balances.tests.helpers import PeriodBalanceWithTransactionsFactory, balance_signals_disabled

class FactoryTestCase(TestCase, BaseTestHelper):
    def setUp(self):
        self.user = self.create_user('testuser', email='testuser@test.com', password='testing')[0]
        self.category = self.create_category('default category')
        self.account = self.create_account()

    def test_factory_creates(self):
        transaction = self.create_transaction(100, date(2016, 1, 10), date(2016, 1, 10))
        create_period_balance_for(transaction, [date(2016, 1, 10)])

        just_created = PeriodBalance.objects.first()
        self.assert_period(
            just_created,
            date(2016, 1, 1),
            date(2016, 1, 31),
            account=transaction.account,
            closed_effective_value=100,
            closed_real_value=100
        )

    def test_factory_creates_without_payment_date(self):
        transaction = self.create_transaction(100, date(2016, 1, 10))
        create_period_balance_for(transaction, [date(2016, 1, 10)])

        just_created = PeriodBalance.objects.first()
        self.assert_period(
            just_created,
            date(2016, 1, 1),
            date(2016, 1, 31),
            account=transaction.account,
            closed_effective_value=100,
            closed_real_value=0
        )

    def test_factory_creates_both_dates(self):
        transaction = self.create_transaction(100, date(2016, 1, 10), date(2016, 3, 20))
        create_period_balance_for(transaction, [date(2016, 1, 10), date(2016, 3, 20)])

        jan_period = PeriodBalance.objects.first()
        mar_period = PeriodBalance.objects.last()

        self.assertEqual(2, len(PeriodBalance.objects.all()))

        self.assert_period(
            jan_period,
            date(2016, 1, 1),
            date(2016, 1, 31),
            account=transaction.account,
            closed_effective_value=100,
            closed_real_value=0
        )

        self.assert_period(
            mar_period,
            date(2016, 3, 1),
            date(2016, 3, 31),
            account=transaction.account,
            closed_effective_value=0,
            closed_real_value=100
        )
        
    def create_transaction(self, value, due_date, payment_date=None):
        with balance_signals_disabled():
            return super().create_transaction(
                value=value,
                due_date=due_date,
                payment_date=payment_date,
            )

    def assert_period(self, period, start, end, **kwargs):
        self.assertEqual(period.start_date, start)
        self.assertEqual(period.end_date, end)

        for key, val in kwargs.items():
            self.assertEqual(getattr(period, key), val)
