from datetime import date
from unittest import mock, skip

from django.test import TestCase

from common.tests_helpers import SerializerTestHelper
from transactions.models import HasKind
from transactions.serializers import TransactionSerializer
from transactions.serializers.PeriodicSerializer import PeriodicSerializer
from transactions.tests.base_test import BaseTestHelperFactory, OtherUserDataTestSetupMixin, UserDataTestSetupMixin


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
            'kind': HasKind.EXPENSE_KIND,
        }
        self.serializer_context = {
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
        data = self.get_data(value=10, kind=HasKind.EXPENSE_KIND)        
        serializer = TransactionSerializer(data=data, context=self.serializer_context)
        self.assert_has_field_error(serializer)

    def test_serializer_value_should_not_allows_income_negative(self):
        data = self.get_data(value=-10, kind=HasKind.INCOME_KIND)        
        serializer = TransactionSerializer(data=data, context=self.serializer_context)
        self.assert_has_field_error(serializer)

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
        data = self.get_data(kind=HasKind.INCOME_KIND)
        serializer = TransactionSerializer(data=data, context=self.serializer_context)
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
