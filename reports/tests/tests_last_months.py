from datetime import datetime
from unittest import mock, skip

from dateutil.relativedelta import relativedelta
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient, APITestCase

from reports.factories.LastMonthsReport import LastMonthsReportFactory
from transactions.models import Category, Transaction
from transactions.tests.base_test import BaseTestHelper


class LastMonthsAPITestCase(TestCase, BaseTestHelper):

    def setUp(self):
        self.user, token = self.create_user('testuser', email='testuser@test.com', password='testing')

        self.client = self.create_authenticated_client(token)
        self.account = self.create_account(self.user)
        self.expense_category = self.create_category('expense-cat')
        self.income_category = self.create_category('income-cat', kind=Category.INCOME_KIND)

    def test_gets_last_12_months_by_default(self):
        response = self.client.get(reverse('last-months'), format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 13)

    def test_gets_last_2_months(self):
        response = self.client.get(reverse('last-months') + '?months=2', format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3) #2 past + current = 3

    @skip('undone')
    def test_gets_last_months_ignores_futures_periods(self):
        pass
    
    @mock.patch('reports.factories.LastMonthsReport.LastMonthsReportFactory.get_start_date', return_value=datetime(2016, 12, 1))
    @mock.patch('reports.factories.LastMonthsReport.LastMonthsReportFactory.get_end_date', return_value=datetime(2017, 12, 31))
    def test_gets_amounts_expent_in_last_months(self, mock_start_date, mock_end_date):
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

        response = self.client.get(reverse('last-months'), format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 13)
        self.assertActualExpected(response.data, expected_list)
        
    @mock.patch('reports.factories.LastMonthsReport.LastMonthsReportFactory.get_start_date', return_value=datetime(2016, 12, 1))
    @mock.patch('reports.factories.LastMonthsReport.LastMonthsReportFactory.get_end_date', return_value=datetime(2017, 12, 31))
    def test_gets_0_when_theres_no_transactions_expent_in_last_months(self, mocked_start_date, mocked_end_date):
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

        response = self.client.get(reverse('last-months'), format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 13)
        self.assertActualExpected(response.data, expected_list)
    
    @mock.patch('reports.factories.LastMonthsReport.LastMonthsReportFactory.get_start_date', return_value=datetime(2017, 1, 1))
    @mock.patch('reports.factories.LastMonthsReport.LastMonthsReportFactory.get_end_date', return_value=datetime(2017, 2, 28))
    def test_gets_amounts_expent_in_last_months_with_overdue(self, mocked_start_date, mocked_end_date):
        #Incomes
        self.create_transaction(50, due_date=datetime(2017, 1, 5),  payment_date=datetime(2017, 2, 5),  category=self.income_category) #Payed one month later only
        self.create_transaction(20, due_date=datetime(2017, 1, 10), payment_date=datetime(2017, 1, 8),  category=self.income_category)
        self.create_transaction(30, due_date=datetime(2017, 2, 15), payment_date=datetime(2017, 2, 15), category=self.income_category)

        #Expenses
        self.create_transaction(-10, due_date=datetime(2017, 1, 6),  payment_date=datetime(2017, 2, 6),  category=self.expense_category) #Payed one month later only
        self.create_transaction(-30, due_date=datetime(2017, 2, 15), payment_date=datetime(2017, 2, 20), category=self.expense_category)

        expected_list = [
            { "period": "2017-01", "effective_expenses": -10, "effective_incomes": 70, "real_expenses": 0, "real_incomes": 20, "effective_total": 60, "real_total": 20 },
            { "period": "2017-02", "effective_expenses": -30, "effective_incomes": 30, "real_expenses": -40, "real_incomes": 80, "effective_total": 0, "real_total": 40 },
        ]

        url = reverse('last-months') + '?payed=1'
        response = self.client.get(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertActualExpected(response.data, expected_list)
    

    def assertActualExpected(self, actual, expected):
        for i in range(len(actual)):
            self.assertEqual(actual[i]['period'], expected[i]['period'])
            self.assertEqual(float(actual[i]["effective_incomes"]), float(expected[i]["effective_incomes"]))
            self.assertEqual(float(actual[i]["effective_expenses"]), float(expected[i]["effective_expenses"]))
            self.assertEqual(float(actual[i]["real_incomes"]), float(expected[i]["real_incomes"]))
            self.assertEqual(float(actual[i]["real_expenses"]), float(expected[i]["real_expenses"]))
            self.assertEqual(float(actual[i]["effective_total"]), float(expected[i]["effective_total"]))
            self.assertEqual(float(actual[i]["real_total"]), float(expected[i]["real_total"]))

class LastMonthsFactoryTestCase(TestCase, BaseTestHelper):    

    def test_generates_reports_filtered_by_user(self):
        user_id = self.create_user_with_transaction('user', 100)
        self.create_user_with_transaction('other_user', 20)

        report_factory = LastMonthsReportFactory(user_id, 13)
        query = report_factory._get_query()
        data = list(query)        

        self.assertEqual(data[0]["effective_total"], 100)

    def create_user_with_transaction(self, name, value):
        user, token = self.create_user(name, email=name+'@test.com', password='pass')
        account = self.create_account(user)
        category = self.create_category('category', user=user, kind=Category.INCOME_KIND)
        self.create_transaction(value, account=account, category=category)
        return user.id
