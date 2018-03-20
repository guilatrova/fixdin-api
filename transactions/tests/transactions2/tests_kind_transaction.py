from datetime import date
from unittest import mock, skip
from unittest.mock import MagicMock
from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework.authtoken.models import Token
from transactions.models import *
from transactions import views
from transactions.serializers import TransactionSerializer, PeriodicSerializer
from transactions.serializers.PeriodicSerializer import PeriodicSerializer
from transactions.factories import create_periodic_transactions, create_transfer_between_accounts
from transactions.tests.base_test import BaseTestHelperFactory, UserDataTestSetupMixin, OtherUserDataTestSetupMixin
from common.tests_helpers import UrlsTestHelper, SerializerTestHelper

class KindTransactionUrlTestCase(TestCase, UrlsTestHelper):

    def test_resolves_list_url(self):
        resolver = self.resolve_by_name('kind_transactions')
        self.assertEqual(resolver.func.cls, views.TransactionViewSet)

    def test_resolves_single_url(self):
        resolver = self.resolve_by_name('kind_transaction', pk=1)
        self.assertEqual(resolver.func.cls, views.TransactionViewSet)

    def test_resolves_list_to_actions(self):
        resolver = self.resolve_by_name('kind_transactions')
        self.assert_resolves_actions(resolver, {
            'get': 'list',
            'post': 'create',
            'delete': 'destroy_all_periodics',
            'patch': 'patch_list'
        })

    def test_list_url_allows_actions(self):
        resolver = self.resolve_by_name('kind_transactions')
        self.assert_has_actions(['get', 'post', 'delete', 'patch'], resolver.func.actions)

    def test_single_url_allows_actions(self):
        resolver = self.resolve_by_name('kind_transaction', pk=1)
        self.assert_has_actions(['get', 'put', 'delete', 'patch'], resolver.func.actions)

class PeriodicSerializerTestCase(TestCase, SerializerTestHelper):
    def setUp(self):
        self.serializer_data = {
            'frequency': 'daily',
            'interval': 1,
        }

    def test_serializer_validates_with_how_many(self):
        data = self.get_data(how_many=2)
        serializer = PeriodicSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_serializer_validates_with_until(self):
        data = self.get_data(until=date(2018, 3, 20))
        serializer = PeriodicSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_serializer_how_many_should_not_allows_below_zero(self):
        data = self.get_data(how_many=0)
        serializer = PeriodicSerializer(data=data)
        self.assert_has_field_error(serializer, 'how_many')

    def test_serializer_should_not_allow_both_until_with_how_many(self):
        data = self.get_data(how_many=2, until=date(2018, 3, 20))
        serializer = PeriodicSerializer(data=data)
        self.assert_has_field_error(serializer)

    def test_serializer_should_not_allow_missing_both_until_with_how_many(self):
        serializer = PeriodicSerializer(data=self.serializer_data)
        self.assert_has_field_error(serializer)

class TransactionSerializerTestCase(UserDataTestSetupMixin, OtherUserDataTestSetupMixin, TestCase, SerializerTestHelper):

    def setUp(self):
        self.serializer_data = {
            'due_date': date(2018, 3, 20),
            'description': 'description',
            'category': self.category.id,
            'value': 0,
            'account': self.account.id,
            'priority': 1,
            'deadline': 1,
        }
        self.serializer_context = {
            'kind': HasKind.EXPENSE_KIND,
            'user_id': self.user.id,
            'request_method': 'POST'
        }

    def test_serializer_only_required_fields_validates(self):
        serializer = TransactionSerializer(data=self.serializer_data, context=self.serializer_context)
        self.assertTrue(serializer.is_valid(raise_exception=True))
    
    def test_serializer_all_fields_validates(self):
        serializer = TransactionSerializer(data=self.get_full_data(), context=self.serializer_context)
        self.assertTrue(serializer.is_valid(raise_exception=True))

    def test_serializer_value_should_not_allows_expense_positive(self):
        data = self.get_data(value=10)
        context = self.get_context(kind=HasKind.EXPENSE_KIND)
        serializer = TransactionSerializer(data=data, context=context)
        self.assert_has_field_error(serializer, 'value')

    def test_serializer_value_should_not_allows_income_negative(self):
        data = self.get_data(value=-10)
        context = self.get_context(kind=HasKind.INCOME_KIND)
        serializer = TransactionSerializer(data=data, context=context)
        self.assert_has_field_error(serializer, 'value')

    def test_serializer_category_should_not_allows_from_other_user(self):
        data = self.get_data(category=self.other_user_data['category'].id)
        serializer = TransactionSerializer(data=data, context=self.serializer_context)
        self.assert_has_field_error(serializer, 'category')

    def test_serializer_account_should_not_allows_from_other_user(self):
        data = self.get_data(account=self.other_user_data['account'].id)
        serializer = TransactionSerializer(data=data, context=self.serializer_context)
        self.assert_has_field_error(serializer, 'account')

    def test_serializer_periodic_cant_be_set_on_put(self):
        data = self.get_data_with_periodic()
        context = self.get_context(request_method='PUT')
        serializer = TransactionSerializer(data=data, context=context)
        self.assert_has_field_error(serializer, 'periodic')

    def test_serializer_should_not_allows_category_kind_different_of_transaction(self):
        context = self.get_context(kind=HasKind.INCOME_KIND)
        serializer = TransactionSerializer(data=self.serializer_data, context=context)
        self.assert_has_field_error(serializer)

    def test_serializer_should_not_allows_periodic_with_until_before_due_date(self):
        data = self.get_data_with_periodic(until=date(2018, 1, 1))
        serializer = TransactionSerializer(data=data, context=self.serializer_context)
        self.assert_has_field_error(serializer)

    def test_serializer_returns_list(self):
        serializer = TransactionSerializer()
        falsy = {}
        truthy = { 'periodic': None }
        self.assertFalse(serializer.is_return_data_list(falsy))
        self.assertTrue(serializer.is_return_data_list(truthy))

    @mock.patch('transactions.factories.create_periodic_transactions')
    def test_serializer_create_periodic(self, create_mock):
        dummy = { 'periodic': None }
        serializer = TransactionSerializer()
        serializer.create(dummy)
        create_mock.assert_called_with(**dummy)

    @mock.patch('rest_framework.serializers.ModelSerializer.create')
    def test_serializer_create_regular(self, super_create_mock):
        dummy = {}
        serializer = TransactionSerializer()
        serializer.create(dummy)
        super_create_mock.assert_called_with(dummy)

    def get_data_with_periodic(self, **kwargs):
        nested = {
            'frequency': 'daily',
            'interval': 1
        }
        nested.update(kwargs)
        data = self.get_data(periodic=nested)
        return data

    def get_full_data(self):
        data = self.get_data_with_periodic(how_many=1)
        data.update({
            'details': 'details',
            'payment_date': date(2018, 3, 20),
        })
        return data

class KindTransactionApiTestMixin(UserDataTestSetupMixin, OtherUserDataTestSetupMixin, BaseTestHelperFactory):
    """
    Exposes all api tests in a generic way. TestCase which inherites this should set some properties.
    By default it creates 2 expenses + 1 income for user, and 2 transactions for another user
    """
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.expense = cls.create_transaction(-100)
        cls.create_transaction(-50)
        cls.income = cls.create_transaction(200, payment_date=date.today(), category=cls.income_category)
        #other user        
        cls.create_transaction(-30, **cls.other_user_data)
        cls.create_transaction(100, **cls.other_user_data)

    def setUp(self):
        self.client = self.create_authenticated_client(self.token)

    def test_api_lists(self):
        response = self.client.get(self.list_url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), self.expected_list_count)

    def test_api_retrieves(self):
        response = self.client.get(self.single_url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.transaction.id)
    
    def test_api_creates(self):
        response = self.client.post(self.list_url, self.dto, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assert_created()

    def test_api_updates(self):
        dto = self.get_updated_dto(description='changed')
        response = self.client.put(self.single_url, dto, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.transaction.refresh_from_db()
        self.assertEqual(self.transaction.description, dto['description'])

    def get_updated_dto(self, **kwargs):
        dto = TransactionSerializer(self.transaction).data
        dto.update(kwargs)
        return dto

class IncomeApiTestCase(KindTransactionApiTestMixin, TestCase):
    expected_list_count = 1    

    @property
    def list_url(self):
        return reverse('kind_transactions', kwargs={'kind': HasKind.INCOME_KIND})

    @property
    def single_url(self):
        return reverse('kind_transaction', kwargs={'kind': HasKind.INCOME_KIND, 'pk': self.transaction.id})

    @property
    def transaction(self):
        return self.income

    @property
    def dto(self):
        return {
            'due_date': date.today(),
            'description': 'dto',
            'category': self.income_category.id,
            'value': 500,
            'details': 'this are the details',
            'account': self.account.id,
            'priority': 1,
            'deadline': 10,
            'payment_date': date.today()
        }
        
    def assert_created(self):
        self.assertEqual(Transaction.objects.incomes().owned_by(self.user).count(), 2)

class ExpenseApiTestCase(KindTransactionApiTestMixin, TestCase):
    expected_list_count = 2

    @property
    def list_url(self):
        return reverse('kind_transactions', kwargs={'kind': HasKind.EXPENSE_KIND})

    @property
    def single_url(self):
        return reverse('kind_transaction', kwargs={'kind': HasKind.EXPENSE_KIND, 'pk': self.transaction.id})

    @property
    def transaction(self):
        return self.expense

    @property
    def dto(self):
        return {
            'due_date': date.today(),
            'description': 'dto',
            'category': self.expense_category.id,
            'value': -500,
            'details': 'this are the details',
            'account': self.account.id,
            'priority': 1,
            'deadline': 10,
            'payment_date': date.today()            
        }

    def assert_created(self):
        self.assertEqual(Transaction.objects.expenses().owned_by(self.user).count(), 3)