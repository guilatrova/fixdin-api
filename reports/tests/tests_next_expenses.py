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
#from reports.factories import Last13MonthsReportFactory

class NextExpensesAPITestCase(TestCase, BaseTestHelper):

    def setUp(self):
        self.user, token = self.create_user('testuser', email='testuser@test.com', password='testing')

        self.client = self.create_authenticated_client(token)
        self.account = self.create_account(self.user)
        self.category = self.create_category('category')

    def test_gets_only_unpaid_expenses(self):
        self.create_transaction(-50, payment_date=datetime.today())
        self.create_transaction(-120, payment_date=datetime.today())
        self.create_transaction(-22, payment_date=datetime.today())
        self.create_transaction(-70)
        self.create_transaction(-30)

        response = self.client.get(reverse('next-expenses'), format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)        