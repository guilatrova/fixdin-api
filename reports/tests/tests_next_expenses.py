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
from reports.factories.NextExpensesReport import NextExpensesReportFactory
from common.helpers import Struct

class NextExpensesAPITestCase(TestCase, BaseTestHelper):

    def setUp(self):
        self.user, token = self.create_user('testuser', email='testuser@test.com', password='testing')

        self.client = self.create_authenticated_client(token)
        self.account = self.create_account(self.user)
        self.category = self.create_category('category')

    def test_gets_only_expenses(self):
        self.create_transaction(-30) #expense
        self.create_transaction(50) #income
        self.create_transaction(70)

        response = self.client.get(reverse('next-expenses'), format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['next']), 1)

    def test_gets_only_unpaid_expenses(self):
        self.create_transaction(-50, payment_date=datetime.today())
        self.create_transaction(-120, payment_date=datetime.today())
        self.create_transaction(-22, payment_date=datetime.today())
        self.create_transaction(-70)
        self.create_transaction(-30)

        response = self.client.get(reverse('next-expenses'), format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['next']), 2)

    @mock.patch('reports.factories.NextExpensesReport.datetime', side_effect=lambda *args, **kw: date(*args, **kw))
    def test_returns_ordered(self, mocked_date):
        '''
        Assert if generated report is ordered by 
        1. Priority; 2. Due_date; 3. Deadline
        '''
        mocked_date.today.return_value = datetime(2017, 1, 2)
        expected_next_order = {}
        expected_overdue_order = {}

        #We are creating those transactions in random order to simulate unordered ids
        #next
        expected_next_order[2] = self.create_transaction(-70, priority=1, due_date=datetime(2017, 1, 2), deadline=10) #3
        expected_next_order[3] = self.create_transaction(-120, priority=1, due_date=datetime(2017, 2, 1), deadline=1) #4
        expected_next_order[1] = self.create_transaction(-30, priority=1, due_date=datetime(2017, 1, 2), deadline=5)  #2
        expected_next_order[0] = self.create_transaction(-100, priority=5, due_date=datetime(2017, 3, 1))             #1

        #overdue
        expected_overdue_order[3] = self.create_transaction(-120, priority=1, due_date=datetime(2016, 2, 1), deadline=1) #4
        expected_overdue_order[0] = self.create_transaction(-100, priority=5, due_date=datetime(2016, 3, 1))             #1
        expected_overdue_order[2] = self.create_transaction(-70, priority=1, due_date=datetime(2016, 1, 2), deadline=10) #3
        expected_overdue_order[1] = self.create_transaction(-30, priority=1, due_date=datetime(2016, 1, 2), deadline=5)  #2

        response = self.client.get(reverse('next-expenses'), format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        report = response.data
        for i in range(len(expected_next_order)):
            self.assertEqual(report['next'][i]['id'], expected_next_order[i].id)

        for i in range(len(expected_overdue_order)):
            self.assertEqual(report['overdue'][i]['id'], expected_overdue_order[i].id)

class NextExpensesFactoryTestCase(TestCase, BaseTestHelper):

    def test_aggregate_by_due_date(self):
        report = NextExpensesReportFactory(1)
        today = datetime.today().date()
        data = [
            { "due_date": today }, #next
            { "due_date": today + relativedelta(days=1) },
            { "due_date": today + relativedelta(months=2) },
            { "due_date": today + relativedelta(days=-1) }, #overdue
            { "due_date": today + relativedelta(months=-1) },
        ]
        expected = {
            "overdue": [
                { "due_date": today + relativedelta(days=-1) },
                { "due_date": today + relativedelta(months=-1) },
            ],
            "next": [
                { "due_date": today },
                { "due_date": today + relativedelta(days=1) },
                { "due_date": today + relativedelta(months=2) }
            ]
        }
        data = [Struct(**x) for x in data]

        aggregated = report.aggregate_by_due_date(data)

        self.assertEqual(len(aggregated['overdue']), len(expected['overdue']))
        self.assertEqual(len(aggregated['next']), len(expected['next']))

        for i in range(len(expected['overdue'])):
            self.assertEqual(aggregated['overdue'][i].due_date, expected['overdue'][i]['due_date'])

        for i in range(len(expected['next'])):
            self.assertEqual(aggregated['next'][i].due_date, expected['next'][i]['due_date'])
        