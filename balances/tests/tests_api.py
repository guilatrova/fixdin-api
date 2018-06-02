from datetime import date, datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch

from dateutil.relativedelta import relativedelta
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient, APITestCase

from transactions.models import *
from transactions.tests.base_test import BaseTestHelperFactory, UserDataTestSetupMixin


class BalanceApiIntegrationTestCase(UserDataTestSetupMixin, APITestCase, BaseTestHelperFactory):

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

class AccountBalanceApiIntegrationTestCase(UserDataTestSetupMixin, APITestCase, BaseTestHelperFactory):

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

class PeriodsBalanceApiIntegrationTestCase(UserDataTestSetupMixin, APITestCase, BaseTestHelperFactory):

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
            
    def test_get_periods(self):
        '''
        Creates 2 transactions/month in a range of 14 months. 
        Then asserts that first month is not retrieved, but all others are
        correctly returned with correct values
        '''
        cumulative_value = 10
        cumulative_date = datetime(2016, 11, 1)

        for i in range(14):
            self.create_transaction(-cumulative_value, due_date=cumulative_date, category=self.expense_category)
            self.create_transaction(-cumulative_value, due_date=cumulative_date, category=self.expense_category)
            self.create_transaction(cumulative_value, due_date=cumulative_date, category=self.income_category)

            cumulative_date = cumulative_date + relativedelta(months=1)
            cumulative_value = cumulative_value + 10

        expected_list = [
            #2016-11 is ignored, but is $20, $10, -$10
            { "period":'2016-12', "effective_expenses":  -40, "effective_incomes":  20, "real_expenses": 0, "real_incomes": 0, "effective_total":  -20, "real_total": 0 },
            { "period":'2017-01', "effective_expenses":  -60, "effective_incomes":  30, "real_expenses": 0, "real_incomes": 0, "effective_total":  -30, "real_total": 0 },
            { "period":'2017-02', "effective_expenses":  -80, "effective_incomes":  40, "real_expenses": 0, "real_incomes": 0, "effective_total":  -40, "real_total": 0 },
            { "period":'2017-03', "effective_expenses": -100, "effective_incomes":  50, "real_expenses": 0, "real_incomes": 0, "effective_total":  -50, "real_total": 0 },
            { "period":'2017-04', "effective_expenses": -120, "effective_incomes":  60, "real_expenses": 0, "real_incomes": 0, "effective_total":  -60, "real_total": 0 },
            { "period":'2017-05', "effective_expenses": -140, "effective_incomes":  70, "real_expenses": 0, "real_incomes": 0, "effective_total":  -70, "real_total": 0 },
            { "period":'2017-06', "effective_expenses": -160, "effective_incomes":  80, "real_expenses": 0, "real_incomes": 0, "effective_total":  -80, "real_total": 0 },
            { "period":'2017-07', "effective_expenses": -180, "effective_incomes":  90, "real_expenses": 0, "real_incomes": 0, "effective_total":  -90, "real_total": 0 },
            { "period":'2017-08', "effective_expenses": -200, "effective_incomes": 100, "real_expenses": 0, "real_incomes": 0, "effective_total": -100, "real_total": 0 },
            { "period":'2017-09', "effective_expenses": -220, "effective_incomes": 110, "real_expenses": 0, "real_incomes": 0, "effective_total": -110, "real_total": 0 },
            { "period":'2017-10', "effective_expenses": -240, "effective_incomes": 120, "real_expenses": 0, "real_incomes": 0, "effective_total": -120, "real_total": 0 },
            { "period":'2017-11', "effective_expenses": -260, "effective_incomes": 130, "real_expenses": 0, "real_incomes": 0, "effective_total": -130, "real_total": 0 },
            { "period":"2017-12", "effective_expenses": -280, "effective_incomes": 140, "real_expenses": 0, "real_incomes": 0, "effective_total": -140, "real_total": 0 },
        ]

        url = reverse('balance-periods') + "?from=2016-12-01&until=2017-12-01"
        response = self.client.get(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 13)
        self.assert_actual_expected(response.data, expected_list)

    def test_get_some_periods_with_0_when_theres_no_transactions_expent_in_period(self):
        '''
        Creates 1 transactions/month in a range of 6 months, skipping 1. 
        Then asserts that all months was filled.
        '''
        cumulative_value = 10
        cumulative_date = datetime(2016, 12, 1)

        for i in range(0, 13, 2):
            self.create_transaction(cumulative_value, due_date=cumulative_date, category=self.expense_category)            

            cumulative_date = cumulative_date + relativedelta(months=2)
            cumulative_value = cumulative_value + 10

        expected_list = [
            { "period":'2016-12', "effective_expenses": 0, "effective_incomes": 10, "real_expenses": 0, "real_incomes": 0, "effective_total": 10, "real_total": 0 },
            { "period":'2017-01', "effective_expenses": 0, "effective_incomes":  0, "real_expenses": 0, "real_incomes": 0, "effective_total": 0 , "real_total": 0 },
            { "period":'2017-02', "effective_expenses": 0, "effective_incomes": 20, "real_expenses": 0, "real_incomes": 0, "effective_total": 20, "real_total": 0 },
            { "period":'2017-03', "effective_expenses": 0, "effective_incomes":  0, "real_expenses": 0, "real_incomes": 0, "effective_total": 0 , "real_total": 0 },
            { "period":'2017-04', "effective_expenses": 0, "effective_incomes": 30, "real_expenses": 0, "real_incomes": 0, "effective_total": 30, "real_total": 0 },
            { "period":'2017-05', "effective_expenses": 0, "effective_incomes":  0, "real_expenses": 0, "real_incomes": 0, "effective_total": 0 , "real_total": 0 },
            { "period":'2017-06', "effective_expenses": 0, "effective_incomes": 40, "real_expenses": 0, "real_incomes": 0, "effective_total": 40, "real_total": 0 },
            { "period":'2017-07', "effective_expenses": 0, "effective_incomes":  0, "real_expenses": 0, "real_incomes": 0, "effective_total": 0 , "real_total": 0 },
            { "period":'2017-08', "effective_expenses": 0, "effective_incomes": 50, "real_expenses": 0, "real_incomes": 0, "effective_total": 50, "real_total": 0 },
            { "period":'2017-09', "effective_expenses": 0, "effective_incomes":  0, "real_expenses": 0, "real_incomes": 0, "effective_total": 0 , "real_total": 0 },
            { "period":'2017-10', "effective_expenses": 0, "effective_incomes": 60, "real_expenses": 0, "real_incomes": 0, "effective_total": 60, "real_total": 0 },
            { "period":'2017-11', "effective_expenses": 0, "effective_incomes":  0, "real_expenses": 0, "real_incomes": 0, "effective_total": 0 , "real_total": 0 },
            { "period":"2017-12", "effective_expenses": 0, "effective_incomes": 70, "real_expenses": 0, "real_incomes": 0, "effective_total": 70, "real_total": 0 },
        ]

        url = reverse('balance-periods') + "?from=2016-12-01&until=2017-12-01"
        response = self.client.get(url, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 13)
        self.assert_actual_expected(response.data, expected_list)
        
    def assert_actual_expected(self, actual, expected):
        for i in range(len(actual)):
            self.assertEqual(actual[i]['period'], expected[i]['period'])
            self.assertEqual(float(actual[i]["effective_incomes"]), float(expected[i]["effective_incomes"]))
            self.assertEqual(float(actual[i]["effective_expenses"]), float(expected[i]["effective_expenses"]))
            self.assertEqual(float(actual[i]["real_incomes"]), float(expected[i]["real_incomes"]))
            self.assertEqual(float(actual[i]["real_expenses"]), float(expected[i]["real_expenses"]))
            self.assertEqual(float(actual[i]["effective_total"]), float(expected[i]["effective_total"]))
            self.assertEqual(float(actual[i]["real_total"]), float(expected[i]["real_total"]))
