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
from transactions.tests.base_test import BaseTestHelperFactory
from common.tests_helpers import UrlsTestHelper, SerializerTestHelper

class KindTransactionUrlTest(TestCase, UrlsTestHelper):

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

#TODO: move from here
class BaseUserDataTestSetupMixin(BaseTestHelperFactory):
    @classmethod
    def setUpTestData(cls):
        cls.user, cls.token = cls.create_user('testuser', email='testuser@test.com', password='testing')
        cls.account = cls.create_account()
        cls.category = cls.create_category('category')
        super().setUpTestData()

#TODO: move from here
class BaseOtherUserDataTestSetupMixin(BaseTestHelperFactory):
    @classmethod
    def setUpTestData(cls):
        other_user, other_token = cls.create_user('other', email='other@test.com', password='pass')
        other_account = cls.create_account(user=other_user)
        other_category = cls.create_category('category', user=other_user)
        cls.other_user = {
            'user': other_user,
            'token': other_token,
            'account': other_account,
            'category': other_category
        }
        super().setUpTestData()

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

class KindTransactionSerializerTestCase(BaseUserDataTestSetupMixin, BaseOtherUserDataTestSetupMixin, TestCase, SerializerTestHelper):

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
        data = self.get_data(category=self.other_user['category'].id)
        serializer = TransactionSerializer(data=data, context=self.serializer_context)
        self.assert_has_field_error(serializer, 'category')

    def test_serializer_account_should_not_allows_from_other_user(self):
        data = self.get_data(account=self.other_user['account'].id)
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

    @mock.patch('transactions.factories.create_periodic_transactions', side_effect=MagicMock())
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

