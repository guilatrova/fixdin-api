from datetime import date

from django.test import TestCase


from balances.models import PeriodBalance
from balances.services import calculator
from transactions.tests.base_test import BaseTestHelper


class CalculatorTestCase(TestCase, BaseTestHelper):
    def setUp(self):
        self.user, token = self.create_user('testuser', email='testuser@test.com', password='testing')

        self.client = self.create_authenticated_client(token)
        self.account = self.create_account(self.user)
        self.category = self.create_category('category')

    def test_calculates_account_current_balance(self):
        self.create_period_balance(date(2017, 12, 1), date(2017, 12, 31), 100, 70)
        self.create_period_balance(date(2018, 1, 1), date(2018, 1, 31), 50, 70)

        result = calculator.calculate_account_current_balance(self.account.id)

        self.assertEqual(result['effective'], 150)
        self.assertEqual(result['real'], 140)

    def test_calculates_account_current_balance_regarding_current_period(self):
        self.create_period_balance(date(2017, 12, 1), date(2017, 12, 31), 100, 70)
        self.create_period_balance(date(2018, 1, 1), date(2018, 1, 31), 50, 70)
        self.create_transaction(300, due_date=date.today(), payment_date=date.today())

        result = calculator.calculate_account_current_balance(self.account.id)

        self.assertEqual(result['effective'], 450)
        self.assertEqual(result['real'], 440)

    def create_period_balance(self, start, end, effective, real):
        PeriodBalance.objects.create(
            account=self.account,
            start_date=start,
            end_date=end,
            closed_effective_value=effective,
            closed_real_value=real
        )
