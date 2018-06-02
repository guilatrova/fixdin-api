from datetime import date

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from transactions import factories
from transactions.models import HasKind, Transaction
from transactions.serializers import TransactionSerializer
from transactions.tests.base_test import BaseTestHelperFactory, OtherUserDataTestSetupMixin, UserDataTestSetupMixin


class ApiTestMixin(UserDataTestSetupMixin, 
                    OtherUserDataTestSetupMixin, 
                    BaseTestHelperFactory):

    kind = HasKind.EXPENSE_KIND
    dto_value = -500

    @property
    def list_url(self):
        return reverse('transactions')

    @property
    def single_url(self):
        return self.get_single_url(self.transaction.id)

    @property
    def dto(self):
        return {
            'due_date': date.today(),
            'description': 'dto',
            'kind': HasKind.EXPENSE_KIND,
            'category': self.transaction.category.id,
            'value': self.dto_value,
            'details': 'this are the details',
            'account': self.account.id,
            'priority': 1,
            'deadline': 10,
            'payment_date': date.today()
        }

    def setUp(self):
        self.client = self.create_authenticated_client(self.token)

    def get_single_url(self, id):
        return reverse('transaction', kwargs={'pk': id})
        
    def assert_count(self, count):
        self.assertEqual(
            Transaction.objects.owned_by(self.user).filter(kind=self.kind).count(),
            count
        )


class OldestTransactionApiTestCase(UserDataTestSetupMixin, APITestCase, BaseTestHelperFactory):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.oldest = cls.create_transaction(-100, due_date=date(2010, 1, 1))
        cls.create_transaction(-5, due_date=date(2014, 1, 1))

    def setUp(self):
        self.client = self.create_authenticated_client(self.token)

    def test_api_retrieves(self):
        response = self.client.get(reverse('oldest-pending-expense'))

        self.assertTrue(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['id'], self.oldest.id)

class TransactionApiTestCase(ApiTestMixin, TestCase):
    expected_list_count = 2
    expected_total_count = 2        

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.transaction = cls.create_transaction(-100)
        cls.create_transaction(-50)
        #other user
        cls.create_transaction(-30, **cls.other_user_data)
        cls.create_transaction(100, **cls.other_user_data)

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
        self.assert_count(self.expected_total_count + 1)

    def test_api_updates(self):
        dto = self.get_updated_dto(description='changed')
        response = self.client.put(self.single_url, dto, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.transaction.refresh_from_db()
        self.assertEqual(self.transaction.description, dto['description'])

    def test_api_deletes(self):
        response = self.client.delete(self.single_url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assert_count(self.expected_total_count - 1)

    def test_api_patches(self):
        dto = { 'description': 'patched' }
        response = self.client.patch(self.single_url, dto, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.transaction.refresh_from_db()
        self.assertEqual(self.transaction.description, dto['description'])

    def test_api_patches_several(self):
        t1 = self.create_transaction(0, kind=self.kind, category=self.transaction.category)
        t2 = self.create_transaction(0, kind=self.kind, category=self.transaction.category)
        ids = ','.join([str(t1.id), str(t2.id)])
        dto = { 'description': 'patched' }
        url = self.list_url + "?ids=" + ids
        response = self.client.patch(url, dto, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        t1.refresh_from_db()
        t2.refresh_from_db()
        self.assertEqual(t1.description, dto['description'])
        self.assertEqual(t2.description, dto['description'])

    def test_api_cant_manage_transfer(self):
        account_to = self.create_account(name='account_to')
        expense, income = factories.create_transfer_between_accounts(self.user.id, account_from=self.account.id, account_to=account_to.id, value=100)
        transaction = income if self.kind == HasKind.INCOME_KIND else expense

        response = self.client.put(self.get_single_url(transaction.id), format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('manage transfers', response.data['detail'])

    def get_dto(self, **kwargs):
        dto = self.dto
        dto.update(kwargs)
        return dto

    def get_updated_dto(self, **kwargs):
        dto = TransactionSerializer(self.transaction).data
        dto.update(kwargs)
        return dto

class PeriodicTransactionApiTestCase(ApiTestMixin, TestCase):
    expected_total_count = 6

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        category = cls.income_category if cls.kind == HasKind.INCOME_KIND else cls.expense_category
        cls.transaction = cls.create_transaction(-100)
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
        self.assert_count(self.expected_total_count + 2)
            
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
        self.assert_count(self.expected_total_count - len(self.periodics))

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
        self.assert_count(self.expected_total_count - 2)

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
