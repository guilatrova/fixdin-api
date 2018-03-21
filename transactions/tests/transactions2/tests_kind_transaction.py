from datetime import date
from unittest import mock, skip
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from transactions.models import Transaction, HasKind
from transactions import views
from transactions.serializers import TransactionSerializer
from transactions import factories
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
            'patch': 'partial_update_list'
        })

    def test_list_url_allows_actions(self):
        resolver = self.resolve_by_name('kind_transactions')
        self.assert_has_actions(['get', 'post', 'delete', 'patch'], resolver.func.actions)

    def test_single_url_allows_actions(self):
        resolver = self.resolve_by_name('kind_transaction', pk=1)
        self.assert_has_actions(['get', 'put', 'delete', 'patch'], resolver.func.actions)

#mixins

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
        self.assert_count(self.expected_list_count + 1)

    def test_api_updates(self):
        dto = self.get_updated_dto(description='changed')
        response = self.client.put(self.single_url, dto, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.transaction.refresh_from_db()
        self.assertEqual(self.transaction.description, dto['description'])

    def test_api_deletes(self):
        response = self.client.delete(self.single_url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assert_count(self.expected_list_count - 1)

    def test_api_patches(self):
        dto = { 'description': 'patched' }
        response = self.client.patch(self.single_url, dto, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.transaction.refresh_from_db()
        self.assertEqual(self.transaction.description, dto['description'])

    def test_api_cant_manage_transfer(self):
        account_to = self.create_account(name='account_to')
        expense, income = factories.create_transfer_between_accounts(self.user.id, account_from=self.account.id, account_to=account_to.id, value=100)
        transaction = income if self.kind == HasKind.INCOME_KIND else expense

        response = self.client.put(self.get_single_url(transaction.id), format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('manage transfers', response.data['detail'])        

    def assert_count(self, count):
        self.assertEqual(
            Transaction.objects.owned_by(self.user).filter(kind=self.kind).count(), 
            count
        )

    @property
    def list_url(self):
        return reverse('kind_transactions', kwargs={'kind': self.kind})

    @property
    def single_url(self):
        return self.get_single_url(self.transaction.id)

    def get_single_url(self, id):
        return reverse('kind_transaction', kwargs={'kind': self.kind, 'pk': id})
    
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

    def get_dto(self, **kwargs):
        dto = self.dto
        dto.update(kwargs)
        return dto

    def get_updated_dto(self, **kwargs):
        dto = TransactionSerializer(self.transaction).data
        dto.update(kwargs)
        return dto

class KindPeriodicApiTestMixin(UserDataTestSetupMixin):
    """
    This mixin implements tests about periodics, but depends on KindTransactionApiTestMixin.
    Creates 5 periodics of kind by default.
    """
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        category = cls.income_category if cls.kind == HasKind.INCOME_KIND else cls.expense_category
        cls.periodics = factories.create_periodic_transactions(**{
            'due_date': date(2018, 3, 21),
            'description': 'periodic',
            'category': category,
            'value': 0,
            'account': cls.account,
            'kind': cls.kind,
            'priority': 1,
            'deadline': 1,
            'periodic': {
                'frequency': 'daily',
                'how_many': 5,
                'interval': 1
            }
        })        

    def test_api_creates_periodics(self):
        dto = self.get_periodic_dto(2)
        response = self.client.post(self.list_url, dto, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(response.data), 2)
        self.assert_count(self.expected_list_count + 2)
            
    def test_api_patches_all_periodics(self):
        url = self.list_url + "?periodic_transaction=" + str(self.periodics[0].id)
        dto = { 'description': 'change it all' }
        response = self.client.patch(url, dto, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assert_changed_periodics(0, 'change it all')
        
    def test_api_deletes_all_periodics(self):
        url = self.list_url + "?periodic_transaction=" + str(self.periodics[0].id)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assert_count(self.expected_list_count - len(self.periodics))

    def test_api_updates_periodic_and_next(self):
        dto = self.get_updated_periodic_dto(3, description='periodic changed')
        url = self.get_single_url(dto['id']) + "?next=1"
        response = self.client.put(url, dto, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assert_changed_periodics(3, 'periodic changed')

    def test_api_deletes_periodic_and_next(self):
        url = self.get_single_url(self.periodics[3].id) + "?next=1"
        response = self.client.delete(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assert_count(self.expected_list_count - 2)

    def assert_changed_periodics(self, split_index, changed):
        for periodic in self.periodics[:split_index]:
            periodic.refresh_from_db()
            self.assertEqual(periodic.description, 'periodic')

        for periodic in self.periodics[split_index:]:
            periodic.refresh_from_db()
            self.assertEqual(periodic.description, changed)

    def get_updated_periodic_dto(self, index, **kwargs):
        dto = TransactionSerializer(self.periodics[index]).data
        dto.update(kwargs)
        return dto

    def get_periodic_dto(self, how_many, **kwargs):
        dto = self.dto
        dto['periodic'] = {'frequency': 'daily', 'how_many': how_many, 'interval': 1}
        dto.update(kwargs)
        return dto

#endmixins

class IncomeApiTestCase(KindTransactionApiTestMixin, KindPeriodicApiTestMixin, TestCase):
    expected_list_count = 6 # 1 + 5 periodics
    kind = HasKind.INCOME_KIND
    dto_value = 200

    @property
    def transaction(self):
        return self.income

class ExpenseApiTestCase(KindTransactionApiTestMixin, KindPeriodicApiTestMixin, TestCase):
    expected_list_count = 7 # 2 + 5 periodics
    kind = HasKind.EXPENSE_KIND
    dto_value = -500

    @property
    def transaction(self):
        return self.expense