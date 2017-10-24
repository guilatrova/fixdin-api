import datetime
from unittest import skip
from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from transactions.models import *
from transactions.tests.base_test import BaseTestHelper
from transactions.factories import create_periodic_transactions

class TransactionSignalsTestCase(TestCase, BaseTestHelper):
    def setUp(self):
        self.user, token = self.create_user('testuser', email='testuser@test.com', password='testing')
        self.category = self.create_category('cat')
        self.account = self.create_account(self.user)

    def test_delete_parent_transaction_updates_all_children_to_next(self):
        transactions = self.create_periodic(4)

        transactions[0].delete()
        self.assertEqual(Transaction.objects.filter(periodic_transaction_id=transactions[0].id).count(), 0)
        self.assertEqual(Transaction.objects.filter(periodic_transaction_id=transactions[1].id).count(), 3)

    def test_delete_child_of_periodic_has_no_side_effect(self):
        transactions = self.create_periodic(4)

        transactions[1].delete()
        self.assertEqual(Transaction.objects.filter(periodic_transaction_id=transactions[0].id).count(), 3)

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