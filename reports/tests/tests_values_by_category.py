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

class ValuesByCategoryAPITestCase(TestCase, BaseTestHelper):
    
    def setUp(self):
        self.user, token = self.create_user('testsuser', email='test@test.com', password='pass')

        self.client = self.create_authenticated_client(token)
        self.account = self.create_account(self.user)

        self.expense_categories = []
        self.income_categories = []
        for i in range(1, 5):
            self.expense_categories.append(self.create_category('EC' + str(i)))
            self.income_categories.append(self.create_category('IC' + str(i), kind=Category.INCOME_KIND))

    @skip('Fast fix')
    def test_gets_values_aggregated_by_expense_category(self):
        cumulative_value = 10
        for i in range(len(self.expense_categories)):
            self.create_transaction(-cumulative_value, category=self.expense_categories[i])
            self.create_transaction(-(cumulative_value * 2), category=self.expense_categories[i])
            cumulative_value += 10

        expected_list = [
            { "category_id": 1, "total": 30 },
            { "category_id": 3, "total": 60 }, #Skip incomes
            { "category_id": 5, "total": 90 },
            { "category_id": 7, "total": 120 },
        ]

        url = reverse('values-by-category', kwargs={'kind': 'expenses'})
        response = self.client.get(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 4)
        for i in range(len(expected_list)):
            self.assertEqual(expected_list[i]["category_id"], response.data[i]["category_id"])
            self.assertEqual(float(expected_list[i]["total"]), float(response.data[i]["total"]))

    @skip('Fast fix')
    def test_gets_values_aggregated_by_income_category(self):
        cumulative_value = 10
        for i in range(len(self.income_categories)):
            self.create_transaction(cumulative_value, category=self.income_categories[i])
            self.create_transaction(cumulative_value * 2, category=self.income_categories[i])
            cumulative_value += 10

        expected_list = [
            { "category_id": 2, "total": 30 }, #Skip expenses
            { "category_id": 4, "total": 60 },
            { "category_id": 6, "total": 90 },
            { "category_id": 8, "total": 120 },
        ]

        url = reverse('values-by-category', kwargs={'kind': 'incomes'})
        response = self.client.get(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 4)
        for i in range(len(expected_list)):
            self.assertEqual(expected_list[i]["category_id"], response.data[i]["category_id"])
            self.assertEqual(float(expected_list[i]["total"]), float(response.data[i]["total"]))

    @skip('DO THIS, ITS IMPORTANT')
    def test_only_calculates_categories_from_authenticated_user(self):
        self.fail('MISSING IMPLEMENTATION')