from datetime import date, datetime
from decimal import Decimal
from dateutil.relativedelta import relativedelta
from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from unittest.mock import patch
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework.authtoken.models import Token
from transactions.models import *
from transactions.tests.base_test import BaseTestHelperFactory

class ApiIntegrationTestCase(TestCase, BaseTestHelperFactory):

    @classmethod
    def setUpTestData(cls):
        cls.user, cls.token = cls.create_user(email='testuser@test.com', password='testing')
        cls.account = cls.create_account(cls.user)
        cls.category = cls.create_category('category')

    def setUp(self):
        self.client = self.create_authenticated_client(self.token)

    def test_get_current_balance(self):
        '''
        Get current balance regardless of payed or not, until present date
        '''
        self.create_transaction(10)
        self.create_transaction(10)
        self.create_transaction(30)
        self.create_transaction(60)
        #tomorrow
        tomorrow = datetime.today() + relativedelta(days=1)
        self.create_transaction(100, due_date=tomorrow)

        response = self.client.get(reverse('balances'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['balance'], 110)

    def test_get_current_real_balance(self):
        '''
        Calculates balance based only in payed transactions
        '''
        self.create_transaction(30, payment_date=datetime.today())
        self.create_transaction(60, payment_date=datetime.today())
        #not payed
        self.create_transaction(10)
        self.create_transaction(10)

        url = reverse('balances') + '?payed=1'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['balance'], 90)

    def test_get_expected_balance_until_date(self):
        self.create_transaction(30, due_date=datetime(2017, 9, 1), payment_date=datetime.today())
        self.create_transaction(60, due_date=datetime(2017, 9, 4), payment_date=datetime.today())
        self.create_transaction(10, due_date=datetime(2017, 9, 15))
        self.create_transaction(25, due_date=datetime(2017, 9, 30))

        url = reverse('balances') + '?until=2017-09-30'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['balance'], 125)

    @patch('balances.queries.date', side_effect=lambda *args, **kw: date(*args, **kw))
    def test_get_total_pending_incomes(self, mock_date):
        mock_date.today.return_value = datetime(2018, 3, 1)
        #ignoreds
        self.create_transaction(-100, due_date=datetime(2018, 3, 1))
        self.create_transaction(100, due_date=datetime(2018, 3, 2))
        self.create_transaction(100, due_date=datetime(2018, 3, 1), payment_date=datetime(2018, 3, 1))
        #considered
        self.create_transaction(100, due_date=datetime(2018, 3, 1))
        self.create_transaction(200, due_date=datetime(2018, 2, 1))

        response = self.client.get(reverse('pending-incomes-balance'))
        self.assert_response(response, 300)

    def assert_response(self, response, balance):
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['balance'], balance)