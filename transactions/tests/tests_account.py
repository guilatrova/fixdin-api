from datetime import date
from unittest import skip
from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework.authtoken.models import Token
from transactions.views import AccountViewSet
from transactions.models import Account
from transactions.serializers import AccountSerializer
from transactions.tests.base_test import BaseTestHelper
from common.tests_helpers import UrlsTestHelper

class AccountUrlTestCase(TestCase, BaseTestHelper, UrlsTestHelper):

    def test_resolves_list_url(self):
        resolver = self.resolve_by_name('accounts')

        self.assertEqual(resolver.func.cls, AccountViewSet)

    def test_resolves_retrieve_url(self):
        resolver = self.resolve_by_name('account', pk=1)

        self.assertEqual(resolver.func.cls, AccountViewSet)

    def test_resolves_url_to_list_action(self):
        resolver = self.resolve_by_name('accounts')

        self.assertIn('get', resolver.func.actions)
        self.assertEqual('list', resolver.func.actions['get'])

    def test_resolves_url_to_retrieve_action(self):
        resolver = self.resolve_by_name('account', pk=1)

        self.assertIn('get', resolver.func.actions)
        self.assertEqual('retrieve', resolver.func.actions['get'])

    def test_list_url_only_allows_get_and_post(self):
        resolver = self.resolve_by_name('accounts')

        self.assert_has_actions(['get', 'post'], resolver.func.actions)

    def test_single_url_allows_all_methods_except_post_patch(self):
        """All methods are: GET and PUT"""
        resolver = self.resolve_by_name('account', pk=1)

        self.assert_has_actions(['get', 'put'], resolver.func.actions)
    
class AccountSerializerTestCase(TestCase, BaseTestHelper):
    def setUp(self):
        self.user, token = self.create_user('testuser', email='testuser@test.com', password='testing')
        self.account = self.create_account(name='acc01')
        self.serializer_data = {
            'name': 'acc02'
        }
        self.serializer_context = {
            'user_id': self.user.id
        }

    def test_serializer_validates(self):
        serializer = AccountSerializer(data=self.serializer_data, context=self.serializer_context)
        self.assertTrue(serializer.is_valid())

    def test_serializer_should_not_allows_repeated_name(self):
        data = self.serializer_data
        data['name'] = 'acc01'

        serializer = AccountSerializer(data=self.serializer_data, context=self.serializer_context)

        self.assertFalse(serializer.is_valid())
        self.assertIn('name', serializer.errors)

    def test_serializer_calculates_balance(self):
        self.category = self.create_category('any')
        self.create_transaction(100, payment_date=date.today())
        serializer = AccountSerializer(self.account)
        self.assertEqual(100, serializer.data['current_balance'])

class AccountApiTestCase(APITestCase, BaseTestHelper):

    def setUp(self):
        self.user, token = self.create_user('testuser', email='testuser@test.com', password='testing')
        self.client = self.create_authenticated_client(token)
        self.account = self.create_account() #Now there are 2 accounts because signals creates a default account 

    def test_api_lists(self):
        response = self.client.get(reverse('accounts'), format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_api_retrieves(self):
        response = self.client.get(reverse('account', kwargs={'pk': self.account.id}))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.account.id)

    def test_api_creates(self):
        dto = {
            'name': 'acc01'
        }

        response = self.client.post(reverse('accounts'), dto, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Account.objects.count(), 3)

    def test_api_updates(self):
        data = {
            'name': 'new_name'
        }
        response = self.client.put(reverse('account', kwargs={'pk': self.account.id}), data=data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expense = Account.objects.get(pk=self.account.id)
        self.assertEqual(expense.name, data['name'])