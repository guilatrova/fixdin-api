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
        