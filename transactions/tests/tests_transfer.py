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
from transactions.serializers import TransferSerializer
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
        self.user, token = self.create_user('testuser', email='testuser@test.com', password='testing')
        self.account_from = self.create_account(name='from')
        self.account_to = self.create_account(name='to')
        self.serializer_data = {
            'account_from': self.account_from.id,
            'account_to': self.account_to.id,
            'value': 100
        }

    def test_serializer_validates(self):
        serializer = TransferSerializer(data=self.serializer_data)
        self.assertTrue(serializer.is_valid())

    def test_account_from_should_exist(self):
        self.assert_validation_account_non_exists('account_from')

    def test_account_to_should_exist(self):
        self.assert_validation_account_non_exists('account_to')

    def test_serializer_should_not_allows_same_from_and_to_accounts(self):
        data = self.serializer_data
        data['account_to'] = data['account_from']

        serializer = TransferSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn('non_field_errors', serializer.errors)

    def assert_validation_account_non_exists(self, key):
        data = self.serializer_data
        data[key] = 22

        serializer = TransferSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn(key, serializer.errors)

class TransferFactory(TestCase, BaseTestHelper):
    def setUp(self):
        self.user, token = self.create_user('testuser', email='testuser@test.com', password='testing')
        self.account_from = self.create_account(name='from')
        self.account_to = self.create_account(name='to')
        self.factory_kwargs = {
            'value': 100
        }
        self.same_properties_keys = ['value', 'description', 'due_date', 'payment_date', 'bound_reason']
    
    def test_creates_transactions_correctly(self):
        result = create_transfer_between_accounts(\
            self.account_from.id,
            self.account_to.id,
            self.user,
            **self.factory_kwargs
        )

        self.assertEqual(2, len(result))

        expense, income = result

        self.assertEqual(expense.kind, HasKind.EXPENSE_KIND)
        self.assertEqual(income.kind, HasKind.INCOME_KIND)

        self.assertEqual(expense.bound_transaction_id, income.id)
        self.assertEqual(income.bound_transaction_id, expense.id)

        self.assertEqual(expense.due_date, expense.payment_date)
        self.assertEqual(expense.bound_reason, BoundReasons.TRANSFER_BETWEEN_ACCOUNTS)
        self.assertEqual(expense.description, BoundReasons.TRANSFER_BETWEEN_ACCOUNTS)

        for key in self.same_properties_keys:
            self.assertEqual(getattr(expense, key), getattr(income, key))

