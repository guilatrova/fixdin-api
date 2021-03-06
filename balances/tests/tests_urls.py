from unittest import skip

from django.test import TestCase

from balances import views
from common.tests_helpers import UrlsTestHelper


class BalancesUrlsTestCase(TestCase, UrlsTestHelper):
    def test_resolves_plain_balance(self):
        resolver = self.resolve_by_name('plain-balance')
        self.assertEqual(resolver.func.cls, views.PlainBalanceAPIView)

    def test_resolves_detailed_balance(self):
        resolver = self.resolve_by_name('detailed-balance')
        self.assertEqual(resolver.func.cls, views.DetailedBalanceAPIView)
    
    @skip('not done')
    def test_resolves_complete_balance(self):
        pass

    def test_resolves_incomes_and_expenses_of_categories(self):
        resolver = self.resolve_by_name('detailed-balance-by-account')
        self.assertEqual(resolver.func.cls, views.DetailedAccountsBalanceAPIView)

    def test_resolves_balance_periods(self):
        resolver = self.resolve_by_name('balance-periods')
        self.assertEqual(resolver.func, views.get_periods)
