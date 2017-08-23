from unittest import skip, mock
from datetime import datetime
from dateutil.relativedelta import relativedelta
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from rest_framework.authtoken.models import Token
from transactions.models import Transaction, Category
from transactions.tests.base_test import BaseTestHelper
from reports.factories.Last13MonthsReport import Last13MonthsReportFactory

class Last13MonthsAPITestCase(TestCase, BaseTestHelper):

    def setUp(self):
        self.user, token = self.create_user('testuser', email='testuser@test.com', password='testing')

        self.client = self.create_authenticated_client(token)
        self.account = self.create_account(self.user)
        self.expense_category = self.create_category('expense-cat')
        self.income_category = self.create_category('income-cat', kind=Category.INCOME_KIND)
    
    @mock.patch('reports.factories.Last13MonthsReport.Last13MonthsReportFactory.get_start_date', return_value=datetime(2016, 12, 1))
    @mock.patch('reports.factories.Last13MonthsReport.Last13MonthsReportFactory.get_end_date', return_value=datetime(2017, 12, 31))
    def test_gets_amounts_expent_in_last_13_months(self, mock_start_date, mock_end_date):
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
            { "period":'2016-12', "expenses":  -40, "incomes":  20, "total":  -20 },
            { "period":'2017-01', "expenses":  -60, "incomes":  30, "total":  -30 },
            { "period":'2017-02', "expenses":  -80, "incomes":  40, "total":  -40 },
            { "period":'2017-03', "expenses": -100, "incomes":  50, "total":  -50 },
            { "period":'2017-04', "expenses": -120, "incomes":  60, "total":  -60 },
            { "period":'2017-05', "expenses": -140, "incomes":  70, "total":  -70 },
            { "period":'2017-06', "expenses": -160, "incomes":  80, "total":  -80 },
            { "period":'2017-07', "expenses": -180, "incomes":  90, "total":  -90 },
            { "period":'2017-08', "expenses": -200, "incomes": 100, "total": -100 },
            { "period":'2017-09', "expenses": -220, "incomes": 110, "total": -110 },
            { "period":'2017-10', "expenses": -240, "incomes": 120, "total": -120 },
            { "period":'2017-11', "expenses": -260, "incomes": 130, "total": -130 },
            { "period":"2017-12", "expenses": -280, "incomes": 140, "total": -140 },
        ]

        response = self.client.get(reverse('last-13-months'), format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 13)
        self.assertActualExpected(response.data, expected_list)
        
    @mock.patch('reports.factories.Last13MonthsReport.Last13MonthsReportFactory.get_start_date', return_value=datetime(2016, 12, 1))
    @mock.patch('reports.factories.Last13MonthsReport.Last13MonthsReportFactory.get_end_date', return_value=datetime(2017, 12, 31))
    def test_gets_0_when_theres_no_transactions_expent_in_last_13_months(self, mocked_start_date, mocked_end_date):
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
            { "period":'2016-12', "expenses": 0, "incomes": 10, "total": 10 },
            { "period":'2017-01', "expenses": 0, "incomes": 0, "total": 0 },
            { "period":'2017-02', "expenses": 0, "incomes": 20, "total": 20 },
            { "period":'2017-03', "expenses": 0, "incomes": 0, "total": 0 },
            { "period":'2017-04', "expenses": 0, "incomes": 30, "total": 30 },
            { "period":'2017-05', "expenses": 0, "incomes": 0, "total": 0 },
            { "period":'2017-06', "expenses": 0, "incomes": 40, "total": 40 },
            { "period":'2017-07', "expenses": 0, "incomes": 0, "total": 0 },
            { "period":'2017-08', "expenses": 0, "incomes": 50, "total": 50 },
            { "period":'2017-09', "expenses": 0, "incomes": 0, "total": 0 },
            { "period":'2017-10', "expenses": 0, "incomes": 60, "total": 60 },
            { "period":'2017-11', "expenses": 0, "incomes": 0, "total": 0 },
            { "period":"2017-12", "expenses": 0, "incomes": 70, "total": 70 },
        ]

        response = self.client.get(reverse('last-13-months'), format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 13)
        self.assertActualExpected(response.data, expected_list)

    
    @mock.patch('reports.factories.Last13MonthsReport.Last13MonthsReportFactory.get_start_date', return_value=datetime(2017, 1, 1))
    @mock.patch('reports.factories.Last13MonthsReport.Last13MonthsReportFactory.get_end_date', return_value=datetime(2017, 2, 28))
    def test_gets_amounts_expent_in_last_13_months_filtered_by_payed(self, mocked_start_date, mocked_end_date):
        #Incomes
        self.create_transaction(50, due_date=datetime(2017, 1, 5), payment_date=datetime(2017, 2, 5), category=self.income_category) #Payed one month later only
        self.create_transaction(20, due_date=datetime(2017, 1, 10), payment_date=datetime(2017, 1, 8), category=self.income_category)
        self.create_transaction(30, due_date=datetime(2017, 2, 15), payment_date=datetime(2017, 2, 15), category=self.income_category)

        #Expenses
        self.create_transaction(-10, due_date=datetime(2017, 1, 6), payment_date=datetime(2017, 2, 6), category=self.expense_category) #Payed one month later only
        self.create_transaction(-30, due_date=datetime(2017, 2, 15), payment_date=datetime(2017, 2, 20), category=self.expense_category)

        expected_list = [
            { "period": "2017-01", "expenses":   0, "incomes": 20, "total": 20 },
            { "period": "2017-02", "expenses": -40, "incomes": 80, "total": 40 },
        ]

        url = reverse('last-13-months') + '?payed=1'
        response = self.client.get(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertActualExpected(response.data, expected_list)

    def assertActualExpected(self, actual, expected):
        for i in range(len(actual)):
            self.assertEqual(actual[i]['period'], expected[i]['period'])
            self.assertEqual(float(actual[i]['incomes']), float(expected[i]['incomes']))
            self.assertEqual(float(actual[i]['expenses']), float(expected[i]['expenses']))
            self.assertEqual(float(actual[i]['total']), float(expected[i]['total']))

class Last13MonthsFactoryTestCase(TestCase, BaseTestHelper):

    @mock.patch('reports.factories.Last13MonthsReport.Last13MonthsReportFactory.get_start_date', return_value=datetime(2016, 12, 1))
    @mock.patch('reports.factories.Last13MonthsReport.Last13MonthsReportFactory.get_end_date', return_value=datetime(2017, 2, 1))
    def test_aggregate_transactions(self, mocked_start, mocked_end):
        data = [
            { "date": datetime(2016, 12, 1).date(), "kind": Transaction.EXPENSE_KIND, "total": -20 },
            { "date": datetime(2016, 12, 1).date(), "kind": Transaction.INCOME_KIND,  "total": 30 },
            { "date": datetime(2017,  1, 1).date(), "kind": Transaction.EXPENSE_KIND, "total": -50 },            
            { "date": datetime(2017,  1, 1).date(), "kind": Transaction.INCOME_KIND,  "total": 10 }
        ]
        expected = [
            { "date": datetime(2016, 12, 1), "expenses": -20, "incomes": 30, "total": 10 },
            { "date": datetime(2017,  1, 1), "expenses": -50, "incomes": 10, "total": -40 },
        ]

        report_factory = Last13MonthsReportFactory(0)
        report = report_factory.aggregate_transactions(data)        
        self.assertEqual(report, expected)

    def test_generates_reports_filtered_by_user(self):
        user_id = self.create_user_with_transaction('user', 100)
        self.create_user_with_transaction('other_user', 20)

        report_factory = Last13MonthsReportFactory(user_id)
        query = report_factory._get_query()
        data = list(query)        

        self.assertEqual(data[0]['total'], 100)

    def create_user_with_transaction(self, name, value):
        user, token = self.create_user(name, email=name+'@test.com', password='pass')
        account = self.create_account(user)
        category = self.create_category('category', user=user, kind=Category.INCOME_KIND)
        self.create_transaction(value, account=account, category=category)
        return user.id