from unittest import skip
from unittest.mock import patch, MagicMock
import datetime
from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from transactions.models import HasKind, BoundReasons, Transaction
from transactions.views import TransferViewSet
from transactions.serializers import TransferSerializer
from transactions.tests.base_test import BaseTestHelper
from transactions.factories import create_transfer_between_accounts

class TransferUrlTestCase(TestCase, BaseTestHelper):

    def test_resolves_list_url(self):
        resolver = self.resolve_by_name('transfers')

        self.assertEqual(resolver.func.cls, TransferViewSet)

    def test_resolves_retrieve_url(self):
        resolver = self.resolve_by_name('transfer', pk=1)

        self.assertEqual(resolver.func.cls, TransferViewSet)

    def test_resolves_url_to_list_action(self):
        resolver = self.resolve_by_name('transfers')

        self.assertIn('get', resolver.func.actions)
        self.assertEqual('list', resolver.func.actions['get'])

    def test_resolves_url_to_retrieve_action(self):
        resolver = self.resolve_by_name('transfer', pk=1)

        self.assertIn('get', resolver.func.actions)
        self.assertEqual('retrieve', resolver.func.actions['get'])        

    def test_list_url_only_allows_get_and_post(self):
        resolver = self.resolve_by_name('transfers')

        self.assert_has_actions(['get', 'post'], resolver.func.actions)

    def test_single_url_allows_all_methods_except_post_patch(self):
        """All methods are: GET, PUT and DELETE"""
        resolver = self.resolve_by_name('transfer', pk=1)

        self.assert_has_actions(['get', 'delete'], resolver.func.actions)

class TransferSerializerTestCase(TestCase, BaseTestHelper):
    def setUp(self):
        self.user, token = self.create_user('testuser', email='testuser@test.com')
        self.account_from = self.create_account(name='from')
        self.account_to = self.create_account(name='to')
        
        other_user, other_token = self.create_user('other_testuser', email='other_testuser@test.com')
        self.not_owned_account = self.create_account(name='not_owned', user=other_user)

        self.serializer_data = {
            'account_from': self.account_from.id,
            'account_to': self.account_to.id,
            'value': 100
        }
        self.serializer_context = {
            'user_id': self.user.id
        }

    def test_serializer_validates(self):
        serializer = TransferSerializer(data=self.serializer_data, context=self.serializer_context)
        self.assertTrue(serializer.is_valid())

    def test_account_from_should_exists(self):
        self.assert_validation_account_non_exists('account_from')

    def test_account_to_should_exists(self):
        self.assert_validation_account_non_exists('account_to')

    def test_serializer_should_not_allows_not_owned_account_from(self):
        self.assert_validation_account_not_owned('account_from', 'does not belongs to you')

    def test_serializer_should_not_allows_not_owned_account_from(self):
        self.assert_validation_account_not_owned('account_to', 'does not belongs to you')

    def test_serializer_should_not_allows_same_from_and_to_accounts(self):
        data = self.serializer_data
        data['account_to'] = data['account_from']

        serializer = TransferSerializer(data=data, context=self.serializer_context)

        self.assertFalse(serializer.is_valid())
        self.assertIn('non_field_errors', serializer.errors)

    def assert_validation_account_non_exists(self, key):
        data = self.serializer_data
        data[key] = 22

        serializer = TransferSerializer(data=data, context=self.serializer_context)

        self.assertFalse(serializer.is_valid())
        self.assertIn(key, serializer.errors)

    def assert_validation_account_not_owned(self, key, partial_message):
        data = self.serializer_data
        data[key] = self.not_owned_account.id

        serializer = TransferSerializer(data=data, context=self.serializer_context)

        self.assertFalse(serializer.is_valid())
        self.assertIn(key, serializer.errors)
        self.assertIn(partial_message, serializer.errors[key][0])

class TransferFactoryTestCase(TestCase, BaseTestHelper):
    def setUp(self):
        self.user, token = self.create_user('testuser', email='testuser@test.com', password='testing')
        self.account_from = self.create_account(name='from')
        self.account_to = self.create_account(name='to')
        self.factory_kwargs = {
            'account_from': self.account_from.id,
            'account_to': self.account_to.id,
            'value': 100
        }
        self.same_properties_keys = ['value', 'description', 'due_date', 'payment_date', 'bound_reason']
    
    def test_creates_transactions_correctly(self):
        result = create_transfer_between_accounts(\
            self.user.id,
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
        self.assertEqual(expense.value, 100)

        for key in self.same_properties_keys:
            self.assertEqual(getattr(expense, key), getattr(income, key))

class TransferApiTestCase(APITestCase, BaseTestHelper):
    def setUp(self):
        self.user, token = self.create_user('testuser', email='testuser@test.com')
        self.client = self.create_authenticated_client(token)

        self.account_from = self.create_account(name='from')
        self.account_to = self.create_account(name='to')
        self.expense, self.income = create_transfer_between_accounts(self.user.id, account_from=self.account_from.id, account_to=self.account_to.id, value=100)

        self.request = MagicMock(user=self.user)
        self.view = TransferViewSet(request=self.request)

    def test_api_lists(self):
        response = self.client.get(reverse('transfers'), format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_api_retrieves(self):
        response = self.client.get(reverse('transfer', kwargs={'pk': self.expense.id}))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.expense.id)

    def test_api_creates(self):
        data = {
            'account_from': self.account_from.id,
            'account_to': self.account_to.id,
            'value': 100
        }
        response = self.client.post(reverse('transfers'), data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Transaction.objects.count(), 4) #2 from setup + 2 now

    def test_api_deletes(self):
        response = self.client.delete(reverse('transfer', kwargs={'pk': self.expense.id}))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Transaction.objects.count(), 0)