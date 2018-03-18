from django.test import TestCase

from common.tests_helpers import UrlsTestHelper
from balances import views

class BalancesUrlsTestCase(TestCase, UrlsTestHelper):

    def test_resolves_current_balance_url(self):
        resolver = self.resolve_by_name('balances')
        self.assertEqual(resolver.func, views.get_balance)

    def test_resolves_pending_incomes_balance(self):
        resolver = self.resolve_by_name('pending-incomes-balance')
        self.assertEqual(resolver.func, views.get_total_pending_incomes)
