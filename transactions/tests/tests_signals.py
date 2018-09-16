import datetime

from django.test import TestCase

from transactions.factories import create_periodic_transactions
from transactions.models import Transaction
from transactions.tests.base_test import BaseTestHelperFactory, WithoutSignalsMixin


class TransactionSignalsTestCase(WithoutSignalsMixin, TestCase, BaseTestHelperFactory):
    signals_except = [WithoutSignalsMixin.TRANSACTION_PERIODICS]

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user, token = cls.create_user('testuser', email='testuser@test.com', password='testing')
        cls.account = cls.create_account()
        cls.category = cls.create_category('cat')

    def test_delete_parent_transaction_updates_all_children_to_next(self):
        transactions = self.create_periodic(4)

        transactions[0].delete()
        self.assertEqual(Transaction.objects.filter(bound_transaction_id=transactions[0].id).count(), 0)
        self.assertEqual(Transaction.objects.filter(bound_transaction_id=transactions[1].id).count(), 3)

    def test_delete_child_of_periodic_has_no_side_effect(self):
        transactions = self.create_periodic(4)

        transactions[1].delete()
        self.assertEqual(Transaction.objects.filter(bound_transaction_id=transactions[0].id).count(), 3)

    def create_periodic(self, how_many):
        return create_periodic_transactions(
            account=self.account,
            category=self.category,
            due_date=datetime.date(2017, 1, 1),
            description='any',
            value=10,
            kind=Transaction.INCOME_KIND,
            payment_date=datetime.date(2017, 1, 1),
            periodic={
                'frequency': 'daily',
                'interval': 1,
                'how_many': how_many,
            })
