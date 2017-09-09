from unittest import mock
import datetime
from unittest import skip
from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework.authtoken.models import Token
from transactions.models import *

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
        transaction = self.create_transaction(value=self.value, payment_date=datetime.date(2017, 7, 20))

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


    @skip('DISABLED IN DEVELOPMENT PHASE')
    @mock.patch('transactions.views.datetime', side_effect=lambda *args, **kw: date(*args, **kw))    
    def test_returns_only_from_current_month_by_default(self, mock_date):
        '''
        Returns only transactions from current month. Considering today is 15/02/2017
        '''
        mocked_today = datetime.datetime(2017, 2, 15)
        mock_date.today.return_value = mocked_today
        
        #old transactions
        self.create_transaction(value=self.value, due_date=datetime.date(2016, 12, 1))
        self.create_transaction(value=self.value, due_date=datetime.date(2017, 1, 1))
        #current month
        self.create_transaction(value=self.value, due_date=datetime.date(2017, 2, 1))
        self.create_transaction(value=self.value, due_date=datetime.date(2017, 2, 7))
        self.create_transaction(value=self.value, due_date=datetime.date(2017, 2, 8))
        self.create_transaction(value=self.value, due_date=datetime.date(2017, 2, 14))

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 4)

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

class TransactionFilterTestMixin:

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

    def test_can_filter_by_multiple_categories(self):
        second_category = self.create_category('Second category')
        third_category = self.create_category('Third category')
        self.create_transaction(value=self.value)
        self.create_transaction(value=self.value)
        self.create_transaction(value=self.value)
        #other categories
        self.create_transaction(value=self.value, category=second_category)        
        self.create_transaction(value=self.value, category=third_category)

        url = '{}?category={},{}'.format(self.url, second_category.id, third_category.id)

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_can_filter_by_payed(self):
        self.create_transaction(value=self.value, payment_date=datetime.date(2016, 1, 1))
        self.create_transaction(value=self.value, payment_date=datetime.date(2017, 2, 1))
        self.create_transaction(value=self.value, payment_date=datetime.date(2017, 4, 2))
        self.create_transaction(value=self.value, payment_date=datetime.date(2017, 5, 10))
        #not payed
        self.create_transaction(value=self.value)

        url = self.url + '?payed=1'

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 4)

    def test_can_filter_by_not_payed(self):
        self.create_transaction(value=self.value, payment_date=datetime.date(2016, 1, 1))
        self.create_transaction(value=self.value, payment_date=datetime.date(2017, 2, 1))
        self.create_transaction(value=self.value, payment_date=datetime.date(2017, 4, 2))
        self.create_transaction(value=self.value, payment_date=datetime.date(2017, 5, 10))
        #not payed
        self.create_transaction(value=self.value)

        url = self.url + '?payed=0'

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_can_filter_both_payed_and_not_payed(self):
        self.create_transaction(value=self.value, payment_date=datetime.date(2016, 1, 1))
        self.create_transaction(value=self.value, payment_date=datetime.date(2017, 2, 1))
        self.create_transaction(value=self.value, payment_date=datetime.date(2017, 4, 2))
        self.create_transaction(value=self.value, payment_date=datetime.date(2017, 5, 10))
        #not payed
        self.create_transaction(value=self.value)

        url = self.url + '?payed=-1'

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 5)

    def test_can_filter_by_payment_date(self):
        self.create_transaction(value=self.value, due_date=datetime.date(2017, 1, 1), payment_date=datetime.date(2017, 2, 1))
        self.create_transaction(value=self.value, due_date=datetime.date(2017, 1, 3), payment_date=datetime.date(2017, 4, 2))
        #not payed or out of range
        self.create_transaction(value=self.value, due_date=datetime.date(2016, 1, 1), payment_date=datetime.date(2016, 1, 1))
        self.create_transaction(value=self.value, due_date=datetime.date(2017, 1, 2))
        self.create_transaction(value=self.value, due_date=datetime.date(2017, 2, 1), payment_date=datetime.date(2017, 5, 10))

        url = self.url + '?payed={}&payment_date_from={}&payment_date_until={}'.format('1', '2017-01-01', '2017-04-30')

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_can_filter_by_description(self):
        self.create_transaction(description='Python', value=self.value)
        self.create_transaction(description='Python Pro', value=self.value)
        self.create_transaction(description='Python Summit', value=self.value)
        #not related to Python
        self.create_transaction(description='React Group', value=self.value)
        self.create_transaction(description='Food', value=self.value)

        url = self.url + '?description=python'

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

    def test_can_filter_by_priority(self):
        self.create_transaction(priority=3)
        self.create_transaction(priority=3)
        #Other than 3
        self.create_transaction(priority=5)
        self.create_transaction(priority=4)
        self.create_transaction(priority=2)
        self.create_transaction(priority=2)
        self.create_transaction(priority=1)
        self.create_transaction(priority=1)

        url = self.url + '?priority=3'

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_can_filter_by_deadline(self):
        self.create_transaction(deadline=15)
        self.create_transaction(deadline=15)
        self.create_transaction(deadline=15)
        #Other than 15
        self.create_transaction(deadline=1)
        self.create_transaction(deadline=2)
        self.create_transaction(deadline=5)
        self.create_transaction(deadline=10)
        self.create_transaction(deadline=16)
        self.create_transaction(deadline=20)
        self.create_transaction(deadline=25)

        url = self.url + '?deadline=15'

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

class TransactionPeriodicTestMixin:

    def test_create_periodic_daily_transactions(self):
        dto = {
            'due_date': '2017-09-09',
            'description': 'repeat daily',
            'category': self.category.id,
            'value': self.value,
            'details': '',
            'account': self.account.id,
            'priority': '3',
            'deadline': '2',
            "periodic": {
                "period": "daily",
                "distance": 1,
            }
        }    