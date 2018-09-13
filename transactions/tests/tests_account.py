from datetime import date
from unittest.mock import MagicMock

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from common.tests_helpers import UrlsTestHelper
from transactions.filters import AccountFilter
from transactions.models import Account
from transactions.serializers import AccountSerializer
from transactions.tests.base_test import BaseTestHelperFactory
from transactions.views import AccountViewSet


class AccountUrlTestCase(TestCase, UrlsTestHelper):

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

    def test_single_url_allows_actions(self):
        resolver = self.resolve_by_name('account', pk=1)
        self.assert_has_actions(['get', 'put', 'patch'], resolver.func.actions)


class AccountSerializerTestCase(TestCase, BaseTestHelperFactory):
    @classmethod
    def setUpTestData(cls):
        cls.user, cls.token = cls.create_user('testuser', email='testuser@test.com', password='testing')
        cls.account = cls.create_account(name='acc01')
        cls.category = cls.create_category('any')

    def setUp(self):
        self.serializer_data = {
            'name': 'acc02',
            'status': Account.ACTIVE,
        }
        self.serializer_context = {
            'user_id': self.user.id
        }

    def test_serializer_has_fields(self):
        expected_fields = ['id', 'name', 'current_effective_balance',
            'current_real_balance', 'current_balance', 'status']
        self.assertEqual(len(expected_fields), len(AccountSerializer.Meta.fields))
        for field in expected_fields:
            self.assertIn(field, AccountSerializer.Meta.fields)

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
        self.create_transaction(100, payment_date=date.today())
        serializer = AccountSerializer(self.account)
        self.assertEqual(100, serializer.data['current_balance'])


class AccountFilterTest(TestCase):
    def setUp(self):
        self.filter = AccountFilter()
        self.filter.request = MagicMock(query_params={})

    def test_filters_none(self):
        filters = self.filter.get_query_params_filter()
        self.assertEqual({}, filters)

    def test_filters_status(self):
        self.filter.request.query_params = {'status': Account.ARCHIVED}
        filters = self.filter.get_query_params_filter()

        self.assertEqual(1, len(filters))
        self.assertIn('status', filters)
        self.assertEqual(Account.ARCHIVED, filters['status'])


class AccountApiTestCase(APITestCase, BaseTestHelperFactory):

    @classmethod
    def setUpTestData(cls):
        cls.user, cls.token = cls.create_user('testuser', email='testuser@test.com', password='testing')
        cls.account = cls.create_account()  # Now there are 2 accounts because signals creates a default account

    def setUp(self):
        self.client = self.create_authenticated_client(self.token)

    def test_api_lists(self):
        response = self.client.get(reverse('accounts'), format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_api_retrieves(self):
        response = self.client.get(reverse('account', kwargs={'pk': self.account.id}))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.account.id)

    def test_api_creates(self):
        dto = {'name': 'acc01'}

        response = self.client.post(reverse('accounts'), dto, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Account.objects.count(), 3)

    def test_api_updates(self):
        data = {'name': 'new_name'}
        response = self.client.put(reverse('account', kwargs={'pk': self.account.id}), data=data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        account = Account.objects.get(pk=self.account.id)
        self.assertEqual(account.name, data['name'])

    def test_api_patches(self):
        data = {'status': Account.ARCHIVED}
        response = self.client.patch(reverse('account', kwargs={'pk': self.account.id}), data=data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        account = Account.objects.get(pk=self.account.id)
        self.assertEqual(account.status, data['status'])
