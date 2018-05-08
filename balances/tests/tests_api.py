from datetime import date, datetime
from decimal import Decimal
from dateutil.relativedelta import relativedelta
from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from unittest.mock import patch, MagicMock
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework.authtoken.models import Token
from transactions.models import *
from transactions.tests.base_test import BaseTestHelperFactory, UserDataTestSetupMixin

class ApiBalanceIntegrationTestCase(UserDataTestSetupMixin, APITestCase, BaseTestHelperFactory):

    def setUp(self):
        self.client = self.create_authenticated_client(self.token)

    def test_get_current_balance(self):
        """Get current balance regardless of payed or not, until present date"""
        self.create_transaction(10)
        self.create_transaction(10)
        self.create_transaction(30)
        self.create_transaction(60)
        #tomorrow
        tomorrow = datetime.today() + relativedelta(days=1)
        self.create_transaction(100, due_date=tomorrow)

        response = self.client.get(reverse('plain-balance'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['balance'], 110)

    def test_get_current_real_balance(self):
        """Calculates balance based only in payed transactions"""
        self.create_transaction(30, payment_date=datetime.today())
        self.create_transaction(60, payment_date=datetime.today())
        #not payed
        self.create_transaction(10)
        self.create_transaction(10)

        url = reverse('plain-balance') + '?based=real'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['balance'], 90)

    def test_get_expected_balance_until_date(self):
        self.create_transaction(30, due_date=datetime(2017, 9, 1), payment_date=datetime.today())
        self.create_transaction(60, due_date=datetime(2017, 9, 4), payment_date=datetime.today())
        self.create_transaction(10, due_date=datetime(2017, 9, 15))
        self.create_transaction(25, due_date=datetime(2017, 9, 30))

        url = reverse('plain-balance') + '?until=2017-09-30'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['balance'], 125)
    
    def test_get_total_pending_incomes(self):
        #ignoreds
        self.create_transaction(-100, due_date=datetime(2018, 3, 1))
        self.create_transaction(100, due_date=datetime(2018, 3, 2))
        self.create_transaction(100, due_date=datetime(2018, 3, 1), payment_date=datetime(2018, 3, 1))
        #considered
        self.create_transaction(100, due_date=datetime(2018, 3, 1))
        self.create_transaction(200, due_date=datetime(2018, 2, 1))

        url = reverse('plain-balance') + '?output=incomes&pending=1'
        response = self.client.get(url)
        self.assert_response(response, 300)
    
    def test_get_total_pending_expenses(self):
        #ignoreds
        self.create_transaction(100, due_date=datetime(2018, 3, 1))
        self.create_transaction(-100, due_date=datetime(2018, 3, 2))
        self.create_transaction(-100, due_date=datetime(2018, 3, 1), payment_date=datetime(2018, 3, 1))
        #considered
        self.create_transaction(-100, due_date=datetime(2018, 3, 1))
        self.create_transaction(-200, due_date=datetime(2018, 2, 1))

        url = reverse('plain-balance') + "?pending=1&output=incomes"
        response = self.client.get(url)
        self.assert_response(response, -300)

    def test_get_accumulated_balance_over_year(self):
        #ignoreds
        self.create_transaction(1000, due_date=datetime(2016, 1, 1))
        self.create_transaction(-500, due_date=datetime(2018, 1, 1))
        #considered
        self.create_transaction(-100, due_date=datetime(2017, 1, 1))
        self.create_transaction(-300, due_date=datetime(2017, 3, 1))
        self.create_transaction(-800, due_date=datetime(2017, 8, 1))
        self.create_transaction(1000, due_date=datetime(2017, 2, 1))
        self.create_transaction(900, due_date=datetime(2017, 7, 1))

        response = self.client.get(reverse('detailed-balance') + "?from=2017-1-1&until=2017-12-31")
        self.assert_detailed_response(response, 1900, -1200, 700)

    def assert_detailed_response(self, response, incomes, expenses, total):
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['expenses'], expenses)
        self.assertEqual(response.data['incomes'], incomes)
        self.assertEqual(response.data['total'], total)

    def assert_response(self, response, balance):
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['balance'], balance)

class ApiAccountBalanceIntegrationTestCase(UserDataTestSetupMixin, APITestCase, BaseTestHelperFactory):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.accounts = [
            cls.account,
            cls.create_account(name='savings'),
            cls.create_account(name='newaccount')
        ]

    def setUp(self):
        self.client = self.create_authenticated_client(self.token)

    def test_get_expenses_incomes_balances_by_category(self):
        payment_date = date.today()
        self.create_transaction(-100, payment_date=payment_date) #by default: first account + today
        self.create_transaction(-200, payment_date=payment_date)
        self.create_transaction(500, payment_date=payment_date)
        self.create_transaction(100, payment_date=payment_date)
        self.create_transaction(-100, account=self.accounts[1], payment_date=payment_date)
        self.create_transaction(-100, account=self.accounts[1], payment_date=payment_date)
        self.create_transaction(500, account=self.accounts[1], payment_date=payment_date)
        self.create_transaction(2500, account=self.accounts[1], payment_date=payment_date)

        response = self.client.get(reverse('detailed-balance-by-account'), format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 4)
        self.assert_balances(response.data[0], self.accounts[0].id, 600, -300, 300)
        self.assert_balances(response.data[1], self.accounts[1].id, 3000, -200, 2800)
        self.assert_balances(response.data[2], False, 0, 0, 0) #Signals creates a default account
        self.assert_balances(response.data[3], False, 0, 0, 0) #Signals creates a default account

    def assert_balances(self, data, account_id, incomes, expenses, total):
        if account_id:
            self.assertEqual(data['account'], account_id)
        self.assertEqual(data['incomes'], incomes)
        self.assertEqual(data['expenses'], expenses)
        self.assertEqual(data['total'], total)

class ApiAccountBalanceIntegrationTestCase(UserDataTestSetupMixin, APITestCase, BaseTestHelperFactory):

    def setUp(self):
        self.client = self.create_authenticated_client(self.token)

    @patch('balances.views.PeriodQueryBuilder', return_value=MagicMock())
    @patch('balances.views.datetime', side_effect=lambda *args, **kw: date(*args, **kw))
    def test_get_without_query_params_uses_default_date(self, date_mock, mock):
        mock.build.return_value = []
        date_mock.today.return_value = datetime(2018, 5, 5)

        url = reverse('balance-periods')
        response = self.client.get(url)

        mock.assert_called_once_with(self.user.id, datetime(2018, 5, 1), datetime(2018, 5, 1))