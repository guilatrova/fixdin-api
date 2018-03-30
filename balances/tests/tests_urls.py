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

    def test_resolves_pending_incomes_balance(self):
        resolver = self.resolve_by_name('pending-expenses-balance')
        self.assertEqual(resolver.func, views.get_total_pending_expenses)

class BalancesAccountUrlsTestCase(TestCase, UrlsTestHelper):

    def test_resolves_incomes_and_expenses_of_categories(self):
        resolver = self.resolve_by_name('effective-incomes-expenses-balance-by-account')
        self.assertEqual(resolver.func, views.get_effective_incomes_expenses_by_account)