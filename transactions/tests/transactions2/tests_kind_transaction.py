from datetime import date
from unittest import mock, skip
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from transactions.models import Transaction, HasKind
from transactions import views
from transactions.serializers import TransactionSerializer
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

class KindTransactionApiTestMixin(UserDataTestSetupMixin, OtherUserDataTestSetupMixin, BaseTestHelperFactory):
    """
    Exposes all api tests in a generic way. TestCase which inherites this should set some properties.
    By default it creates 2 expenses + 1 income for user, and 2 transactions for another user.
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

    @property
    def list_url(self):
        return reverse('kind_transactions', kwargs={'kind': self.kind})

    @property
    def single_url(self):
        return reverse('kind_transaction', kwargs={'kind': self.kind, 'pk': self.transaction.id})

    def get_updated_dto(self, **kwargs):
        dto = TransactionSerializer(self.transaction).data
        dto.update(kwargs)
        return dto
    
    @property
    def dto(self):
        return {
            'due_date': date.today(),
            'description': 'dto',
            'category': self.transaction.category.id,
            'value': self.dto_value,
            'details': 'this are the details',
            'account': self.account.id,
            'priority': 1,
            'deadline': 10,
            'payment_date': date.today()
        }

class IncomeApiTestCase(KindTransactionApiTestMixin, TestCase):
    expected_list_count = 1
    kind = HasKind.INCOME_KIND
    dto_value = 200

    @property
    def transaction(self):
        return self.income
        
    def assert_created(self):
        self.assertEqual(Transaction.objects.incomes().owned_by(self.user).count(), 2)

class ExpenseApiTestCase(KindTransactionApiTestMixin, TestCase):
    expected_list_count = 2
    kind = HasKind.EXPENSE_KIND
    dto_value = -500

    @property
    def transaction(self):
        return self.expense

    def assert_created(self):
        self.assertEqual(Transaction.objects.expenses().owned_by(self.user).count(), 3)