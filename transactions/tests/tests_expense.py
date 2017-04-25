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
        TransactionTestMixin.setUp(self)
        
        self.url = '/api/v1/expenses/'
        self.value = -40

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

        response = self.client.post(self.url, transaction_dto, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Transaction.objects.count(), 0)

    def get_dto(self):
        return {
            'due_date': '2017-04-13',
            'description': 'gas',
            'category': self.category.id,
            'value': -40,
            'payed': False,
            'details': '',
            'account': self.account.id
        }