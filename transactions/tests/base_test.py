import datetime
from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework.authtoken.models import Token
from transactions.models import *

class BaseTestHelper:
    '''
    Class used to create some resources to backup tests
    '''
    def create_transaction(self, value=-40, description='description', kind=None, account=None, category=None):
        if account is None:
            account = self.account

        if category is None:
            category = self.category

        if kind is None:
            kind = Transaction.EXPENSE_KIND if value <= 0 else Transaction.INCOME_KIND

        transaction = Transaction.objects.create(
            account=account,
            due_date=datetime.date(2017, 1, 1),
            description=description,
            category=category,
            value=value,
            kind=kind
            )

        return transaction

    def create_account(self, user=None):
        if user is None:
            user = self.user

        return Account.objects.create(name='default', user=user, current_balance=0)

    def create_user(self, name='testuser', **kwargs):
        user = User.objects.create_user(kwargs)
        token = Token.objects.get(user=user)

        return user, token

    def create_category(self, name, user=None, kind=Category.EXPENSE_KIND):
        if user is None:
            user = self.user

        return Category.objects.create(kind=kind, user=user, name=name)

class TransactionTestMixin:

    def setUp(self):
        self.user, token = self.create_user('testuser', email='testuser@test.com', password='testing')

        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        self.account = self.create_account(self.user)
        self.category = self.create_category('car')        
        
    def test_create_transaction(self):
        transaction_dto = self.get_dto()

        response = self.client.post(self.url, transaction_dto, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Transaction.objects.count(), 1)

    def test_update_transaction(self):
        transaction = self.create_transaction(value=self.value)

        transaction_dto = self.get_dto()
        transaction_dto['id'] = transaction.id
        transaction_dto['description'] = 'changed'

        url = self.url + str(transaction.id)
        response = self.client.put(url, transaction_dto, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Transaction.objects.all().first().description, transaction_dto['description'])
    
    def test_retrieve_transaction(self):
        transaction = self.create_transaction(value=self.value)

        url = self.url + str(transaction.id)
        response = self.client.get(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(transaction.id, response.data['id'])
        self.assertEqual(transaction.due_date.strftime("%Y-%m-%d"), response.data['due_date'])
        self.assertEqual(transaction.description, response.data['description'])
        self.assertEqual(transaction.value, float(response.data['value']))
        self.assertEqual(transaction.priority, float(response.data['priority']))
        self.assertEqual(transaction.deadline, float(response.data['deadline']))

    def test_delete_transaction(self):
        transaction = self.create_transaction(value=self.value)

        url = self.url + str(transaction.id)
        response = self.client.delete(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Transaction.objects.filter(id=transaction.id).exists())

    def test_list_users_transactions(self):
        '''
        Should list only user's transactions without listing data from others users
        '''
        #Other user
        other_user, other_user_token = self.create_user('other user', username='other', password='123456')
        other_user_account = self.create_account(user=other_user)
        self.create_transaction(value=self.value, account=other_user_account)
        
        self.create_transaction(value=self.value)
        self.create_transaction(value=self.value)
        self.create_transaction(value=self.value)

        response = self.client.get(self.url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

    def test_userX_cant_create_expense_on_userY_account(self):
        userX, userX_token = self.create_user('userX', email='userX@hotmail.com', password='userX')
        
        userX_client = APIClient()
        userX_client.credentials(HTTP_AUTHORIZATION='Token' + userX_token.key)

        transaction_dto = {
            'due_date': '2017-04-13',
            'description': 'gas',
            'category': self.category.id,
            'value': 0,
            'details': '',
            'account': self.account.id
        }

        response = userX_client.post(self.url, transaction_dto, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_userX_cant_create_expense_with_userY_category(self):
        userX, userX_token = self.create_user('userX', email='userX@hotmail.com', password='userX')
        
        userX_client = APIClient()
        userX_client.credentials(HTTP_AUTHORIZATION='Token' + userX_token.key)

        category = self.create_category('Work')

        transaction_dto = {
            'due_date': '2017-04-13',
            'description': 'gas',
            'category': category.id,
            'value': 0,
            'details': '',
            'account': userX.id
        }

        response = userX_client.post(self.url, transaction_dto, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def get_dto(self):
        return {
            'due_date': '2017-04-13',
            'description': 'gas',
            'category': self.category.id,
            'value': self.value,            
            'details': '',
            'account': self.account.id,
            'priority': '3',
            'deadline': '2'
        }