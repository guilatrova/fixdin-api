from unittest import skip
import datetime
from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework.authtoken.models import Token
from transactions.models import HasKind, BoundReasons
from transactions.views import TransferViewSet
from transactions.serializers import AccountSerializer
from transactions.tests.base_test import BaseTestHelper
from transactions.factories import create_transfer_between_accounts

class TransferUrlTestCase(TestCase, BaseTestHelper):

    def test_resolves_list_url(self):
        resolver = self.resolve_by_name('transfers')

        self.assertEqual(resolver.func.cls, TransferViewSet)

    def test_resolves_url_to_list_action(self):
        resolver = self.resolve_by_name('transfers')

        self.assertIn('get', resolver.func.actions)
        self.assertEqual('list', resolver.func.actions['get'])

    def test_list_url_only_allows_get_and_post(self):
        resolver = self.resolve_by_name('transfers')

        self.assert_has_actions(['get', 'post'], resolver.func.actions)

class TransferSerializerTestCase(TestCase, BaseTestHelper):
    def setUp(self):
        self.serializer_data = {
            '': ''
        }

    def test_serializer_validates(self):
        pass

class TransferFactory(TestCase, BaseTestHelper):
    def setUp(self):
        self.user, token = self.create_user('testuser', email='testuser@test.com', password='testing')
        self.account_from = self.create_account(name='from')
        self.account_to = self.create_account(name='to')
        self.factory_kwargs = {
            'due_date': datetime.datetime.today(),
            'description': 'transfer',
            'value': 100
        }
        self.same_properties_keys = ['value', 'description', 'due_date', 'details', 'payment_date', 'bound_reason']
    
    def test_creates_transactions_correctly(self):
        result = create_transfer_between_accounts(\
            self.account_from.id,
            self.account_to.id,
            self.user,
            **self.factory_kwargs
        )

        self.assertEqual(2, len(result))
        self.assertEqual(result[0].kind, HasKind.EXPENSE_KIND)
        self.assertEqual(result[1].kind, HasKind.INCOME_KIND)

        self.assertEqual(result[0].bound_transaction_id, result[1].id)
        self.assertEqual(result[1].bound_transaction_id, result[0].id)

        self.assertEqual(result[0].due_date, result[0].payment_date)
        self.assertEqual(result[0].bound_reason, BoundReasons.TRANSFER_BETWEEN_ACCOUNTS)

        for key in self.same_properties_keys:
            self.assertEqual(getattr(result[0], key), getattr(result[1], key))

