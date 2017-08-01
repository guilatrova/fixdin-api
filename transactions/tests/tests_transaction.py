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

class TransactionTestCase(APITestCase, BaseTestHelper):
    '''
    Tests a generic endpoint /transactions that only retrieves/lists transactions
    regardless of its kind
    '''
    def setUp(self):
        self.user, token = self.create_user('testuser', email='testuser@test.com', password='testing')
        self.client = self.create_authenticated_client(token)
        self.account = self.create_account(self.user)

        self.income_category = self.create_category('salary', kind=Category.INCOME_KIND)
        self.expense_category = self.create_category('dinner', kind=Category.EXPENSE_KIND)

    def test_lists_both_incomes_and_expenses(self):
        # Expenses
        self.create_transaction(value=-100,category=self.expense_category) 
        self.create_transaction(value=-50,category=self.expense_category)
        # Incomes
        self.create_transaction(value=220,category=self.income_category)
        self.create_transaction(value=200,category=self.income_category)

        response = self.client.get(reverse('transactions'), format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 4)

    def test_retrieves_both_incomes_and_expenses(self):
        expense = self.create_transaction(value=-100,category=self.expense_category) #Expense
        income = self.create_transaction(value=220,category=self.income_category) #Incomes

        income_url = reverse('transaction', kwargs={'pk':income.id})
        expense_url = reverse('transaction', kwargs={'pk':expense.id})

        response = self.client.get(income_url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)        
        self.assertEqual(response.data['value'], '220.00')

        response = self.client.get(expense_url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['value'], '-100.00')