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

class IncomeTestCase(APITestCase, TransactionTestMixin, TransactionFilterTestMixin, TransactionPeriodicTestMixin, BaseTestHelper):
    '''
    Tests a lot of operations in /incomes endpoint and some specific rules
    valid only for this endpoint
    '''
    url_single_resource_name = 'expense'
    url_list_resource_name = 'expenses'

    def setUp(self):
        TransactionTestMixin.setUp(self)

        income_category = self.create_category('salary', kind=Category.INCOME_KIND)
        expense_category = self.create_category('dinner', kind=Category.EXPENSE_KIND)

        self.url = '/api/v1/incomes/'
        self.value = 40
        self.category = income_category
        self.inverse_category = expense_category

    def test_cant_create_income_lower_than_0(self):
        transaction_dto = {
            'due_date': '2017-04-13',
            'description': 'gas',
            'category': self.category.id,
            'value': -5,
            'payed': False,
            'details': '',
            'account': self.account.id
        }

        response = self.client.post(self.url, transaction_dto, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Transaction.objects.count(), 0)

    def test_list_only_incomes(self):
        '''
        Should list only user's INCOMES without listing expenses
        '''               
        self.create_transaction(value=-100) #expense
        self.create_transaction(value=0, kind=Transaction.INCOME_KIND)
        self.create_transaction(value=self.value)
        self.create_transaction(value=self.value)

        response = self.client.get(self.url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)