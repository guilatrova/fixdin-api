import datetime
from unittest import skip
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
    def create_transaction(self, value=-40, description='description', kind=None, account=None, category=None, due_date=None):
        if account is None:
            account = self.account

        if category is None:
            category = self.category

        if due_date is None:
            due_date = datetime.date(2017, 1, 1)

        if kind is None:
            kind = Transaction.EXPENSE_KIND if value <= 0 else Transaction.INCOME_KIND

        transaction = Transaction.objects.create(
            account=account,
            due_date=due_date,
            description=description,
            category=category,
            value=value,
            kind=kind,
            payment_date=datetime.date(2017, 1, 2)
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

        self.client = self.create_authenticated_client(token)

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
        self.assertEqual(transaction.payment_date.strftime("%Y-%m-%d"), response.data['payment_date'])

    def test_delete_transaction(self):
        transaction = self.create_transaction(value=self.value)

        url = self.url + str(transaction.id)
        response = self.client.delete(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Transaction.objects.filter(id=transaction.id).exists())

    def test_cant_create_transaction_with_crossed_category(self):
        transaction_dto = self.get_dto(self.inverse_category)        

        response = self.client.post(self.url, transaction_dto, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)       

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

    @skip('Account is setted automatically, later we will disable this and turn on the test')
    def test_user_x_cant_create_transaction_on_user_self_account(self):
        '''
        User can't create a transaction using the credentials from another user.
        '''
        user_x, user_x_token = self.create_user('user_x', email='user_x@hotmail.com', password='user_x')
        category_x = self.create_category('X category', user=user_x, kind=self.category.kind)

        user_x_client = self.create_authenticated_client(user_x_token)

        transaction_dto = {
            'due_date': '2017-04-13',
            'description': 'gas',
            'category': category_x.id,
            'value': 0,
            'details': '',
            'account': self.account.id
        }

        response = user_x_client.post(self.url, transaction_dto, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_x_cant_create_transaction_with_user_self_category(self):
        '''
        User can't create a transaction using the category from another user.
        '''
        user_x, user_x_token = self.create_user('user_x', email='user_x@hotmail.com', password='user_x')
        user_x_account = self.create_account(user_x)
        user_x_client = self.create_authenticated_client(user_x_token)

        transaction_dto = {
            'due_date': '2017-04-13',
            'description': 'gas',
            'category': self.category.id,
            'value': 0,
            'details': '',
            'account': user_x_account.id
        }

        response = user_x_client.post(self.url, transaction_dto, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
    def test_can_create_transaction_with_value_0(self):
        transaction_dto = {
            'due_date': '2017-04-13',
            'description': 'gas',
            'category': self.category.id,
            'value': 0,
            'details': '',
            'account': self.account.id
        }

        response = self.client.post(self.url, transaction_dto, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Transaction.objects.count(), 1)

    def test_can_create_transaction_with_payment_date(self):
        transaction_dto = {
            'due_date': '2017-04-13',
            'description': 'gas',
            'category': self.category.id,
            'value': self.value,            
            'details': '',
            'account': self.account.id,
            'priority': '3',
            'deadline': '2',
            'payment_date': '2017-04-13'
        }

        response = self.client.post(self.url, transaction_dto, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Transaction.objects.count(), 1)

    def test_can_filter_by_due_date(self):
        self.create_transaction(value=self.value, due_date=datetime.date(2017, 1, 1))
        self.create_transaction(value=self.value, due_date=datetime.date(2017, 1, 1))        
        self.create_transaction(value=self.value, due_date=datetime.date(2017, 1, 2))
        #other days
        self.create_transaction(value=self.value, due_date=datetime.date(2017, 1, 3))
        self.create_transaction(value=self.value, due_date=datetime.date(2017, 2, 1))

        url = self.url + '?due_date_from=2017-1-1&due_date_until=2017-1-2'

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

    def test_can_filter_by_category(self):
        second_category = self.create_category('Second category')
        self.create_transaction(value=self.value)
        self.create_transaction(value=self.value)
        self.create_transaction(value=self.value)
        #other categories
        self.create_transaction(value=self.value, category=second_category)        
        self.create_transaction(value=self.value, category=second_category)

        url = '{}?category={}'.format(self.url, self.category.id)

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

    def get_dto(self, category=None):
        if category is None:
            category = self.category

        return {
            'due_date': '2017-04-13',
            'description': 'gas',
            'category': category.id,
            'value': self.value,            
            'details': '',
            'account': self.account.id,
            'priority': '3',
            'deadline': '2'
        }

    def create_authenticated_client(self, token):
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        return client