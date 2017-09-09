import datetime
from unittest import skip
from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework.authtoken.models import Token
from transactions.models import *
from transactions.tests.base_test import BaseTestHelper
from transactions.tests.transactions.mixins import *

class ExpenseTestCase(APITestCase, TransactionTestMixin, TransactionFilterTestMixin, TransactionPeriodicTestMixin, BaseTestHelper):
    '''
    Tests a lot of operations in /expenses endpoint and some specific rules
    valid only for this endpoint
    '''
    def setUp(self):
        TransactionTestMixin.setUp(self)       
         
        income_category = self.create_category('salary', kind=Category.INCOME_KIND)
        
        self.url = '/api/v1/expenses/'
        self.value = -40
        self.inverse_category = income_category

    def test_cant_create_expense_greater_than_0(self):
        transaction_dto = {
            'due_date': '2017-04-13',
            'description': 'gas',
            'category': self.category.id,
            'value': 10,
            'details': '',
            'account': self.account.id
        }

        response = self.client.post(self.url, transaction_dto, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Transaction.objects.count(), 0)

    def test_list_only_expenses(self):
        '''
        Should list only user's EXPENSES without listing incomes
        '''               
        self.create_transaction(value=10) #income
        self.create_transaction(value=self.value)
        self.create_transaction(value=self.value)
        self.create_transaction(value=self.value)

        response = self.client.get(self.url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)