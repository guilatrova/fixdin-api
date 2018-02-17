import calendar
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from unittest import skip
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.db import transaction as db_transaction
from django.db.models import signals
from balances.models import PeriodBalance
from transactions.tests.base_test import BaseTestHelper
from transactions.models import *
from balances.strategies.BaseStrategy import BaseStrategy
from balances.strategies.actions import UPDATED

class BaseStrategyTestCase(TestCase):
    
    @patch.multiple(BaseStrategy, __abstractmethods__=set()) #Allow instantiate abstract class
    def setUp(self):
        self.strategy = BaseStrategy(MagicMock(), UPDATED)

    def test_get_due_date_lower_date(self):
        self.strategy.instance.due_date = date(2014, 8, 22)
        self.strategy.instance.payment_date = date(2017, 1, 1)

        self.assertEqual(self.strategy.get_lower_date(), self.strategy.instance.due_date)

    
    def test_get_payment_date_lower_date(self):
        self.strategy.instance.due_date = date(2014, 8, 22)
        self.strategy.instance.payment_date = date(2010, 1, 1)

        self.assertEqual(self.strategy.get_lower_date(), self.strategy.instance.payment_date)

# class StrategyTestCase(TestCase, BaseTestHelper):
#     def setUp(self):
#         self.strategy = 

#     def test_is_missing_period_returns_true(self):
#         value = date(2016, 1, 10)
#         self.assertTrue(is_missing_period(value))

#     def test_is_missing_period_returns_false(self):
#         PeriodBalance.objects.create(
#             account=self.account,
#             start_date=date(2016, 1, 1),
#             end_date=date(2016, 1, 31),
#             closed_effective_value=10,
#             closed_real_value=10,
#         )
#         value = date(2016, 1, 10)

#         self.assertFalse(is_missing_period(value))