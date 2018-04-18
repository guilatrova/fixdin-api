from django.test import TestCase
from common.tests_helpers import UrlsTestHelper
from balances import views

class BalancesUrlsTestCase(TestCase, UrlsTestHelper):
    def test_resolves_plain_balance(self):
        resolver = self.resolve_by_name('plain-balance')
        self.assertEqual(resolver.func.cls, views.PlainBalanceAPIView)

    def test_resolves_detailed_balance(self):
        resolver = self.resolve_by_name('detailed-balance')
        self.assertEqual(resolver.func.cls, views.DetailedBalanceAPIView)

    def test_resolves_incomes_and_expenses_of_categories(self):
        resolver = self.resolve_by_name('detailed-balance-by-account')
        self.assertEqual(resolver.func.cls, views.DetailedAccountsBalanceAPIView)
