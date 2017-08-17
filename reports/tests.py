from unittest import skip
from unittest import mock
from datetime import datetime
from dateutil.relativedelta import relativedelta
from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from django.db import transaction
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework.authtoken.models import Token
from transactions.models import *
from transactions.tests.base_test import BaseTestHelper

class BalanceTestCase(TestCase, BaseTestHelper):

    def setUp(self):
        self.user, token = self.create_user('testuser', email='testuser@test.com', password='testing')

        self.client = self.create_authenticated_client(token)
        self.account = self.create_account(self.user)
        self.expense_category = self.create_category('expense-cat')        

    @mock.patch('reports.views.Last30MonthsAPIView.get_start_date', return_value=datetime(2016, 12, 1))
    def test_get_amounts_expent_in_last_13_months(self, mock_date):
        '''
        Creates 2 transactions/month in a range of 14 months. 
        Then asserts that first month is not retrieve, but all others are
        correctly returned with correct values
        '''
        cumulative_value = 10
        cumulative_date = datetime(2016, 11, 1)

        for i in range(14):
            self.create_transaction(cumulative_value, due_date=cumulative_date, category=self.expense_category)
            self.create_transaction(cumulative_value, due_date=cumulative_date, category=self.expense_category)

            cumulative_date = cumulative_date + relativedelta(months=1)
            cumulative_value = cumulative_value + 10

        expected_list = [
            { "period":'2016-12', "total": 40 },
            { "period":'2017-01', "total": 60 },
            { "period":'2017-02', "total": 80 },
            { "period":'2017-03', "total": 100 },
            { "period":'2017-04', "total": 120 },
            { "period":'2017-05', "total": 140 },
            { "period":'2017-06', "total": 160 },
            { "period":'2017-07', "total": 180 },
            { "period":'2017-08', "total": 200 },
            { "period":'2017-09', "total": 220 },
            { "period":'2017-10', "total": 240 },
            { "period":'2017-11', "total": 260 },
            { "period":"2017-12", "total": 280 },
            #2016-11 is ignored, but is $ 20
        ]

        response = self.client.get(reverse('last-13-months'), format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 13)
        for i in range(len(response.data)):
            self.assertEqual(response.data[i]['period'], expected_list[i]['period'])
            self.assertEqual(float(response.data[i]['total']), float(expected_list[i]['total']))
        