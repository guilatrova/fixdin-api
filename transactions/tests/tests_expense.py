import datetime
from unittest import skip
from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework.authtoken.models import Token
from transactions.models import *
from transactions.tests.base_test import BaseTestHelper, TransactionTestMixin

class ExpenseTestCase(APITestCase, TransactionTestMixin, BaseTestHelper):

    def setUp(self):
        self.user, token = self.create_user('testuser', email='testuser@test.com', password='testing')

        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        self.account = self.create_account(self.user)
        self.category = self.create_category('car')
        # super(ExpenseTestCase, self).setUp()
        # self.url_single_resource_name = 'expense'
        # self.url_list_resource_name = 'expenses'

    def test_cant_create_expense_greater_than_0(self):
        transaction_dto = {
            'due_date': '2017-04-13',
            'description': 'gas',
            'category': self.category.id,
            'value': 10,
            'payed': False,
            'details': '',
            'account': self.account.id
        }

        response = self.client.post(reverse('transactions'), transaction_dto, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Transaction.objects.count(), 0)