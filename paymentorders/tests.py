from django.test import TestCase
from paymentorders.services import NextExpensesService

from datetime import date, datetime
from decimal import Decimal
from dateutil.relativedelta import relativedelta
from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework.authtoken.models import Token
from unittest import skip
from transactions.models import *
from transactions.tests.base_test import BaseTestHelperFactory

class NextExpensesServiceTestCase(TestCase, BaseTestHelperFactory):

    @classmethod
    def setUpTestData(cls):
        cls.user, token = cls.create_user(email='testuser@test.com', password='testing')
        cls.category = cls.create_category('category')
        cls.account = cls.create_account()

        cls.other_user, other_user_token = cls.create_user('other', email='other@test.com', password='other')
        cls.other_category = cls.create_category('other', user=cls.other_user)
        cls.other_account = cls.create_account(cls.other_user)

    def setUp(self):
        pass

    def test_returns_transactions_from_user(self):
        self.create_transaction(-100, 'user', due_date=date(2018, 1, 1))
        self.create_transaction(-200, 'otheruser', due_date=date(2018, 1, 1), account=self.other_account, category=self.other_category)

        service = NextExpensesService(self.user.id, date(2018, 1, 1), date(2018, 3, 1))
        data = service._generate_queryset()

        self.assertEqual(len(data), 1)
        
    def test_returns_transactions_until_date(self):
        self.create_transaction(-100, '1', due_date=date(2018, 1, 1))
        self.create_transaction(-100, '2', due_date=date(2018, 4, 1))

        service = NextExpensesService(self.user.id, date(2018, 1, 1), date(2018, 3, 1))
        data = service._generate_queryset()

        self.assertEqual(len(data), 1)

    def test_returns_transactions_with_trunc_dates(self):
        self.create_transaction(-100, '1', due_date=date(2018, 1, 5))
        self.create_transaction(-100, '2', due_date=date(2018, 2, 10))
        self.create_transaction(-100, '3', due_date=date(2018, 3, 15))

        service = NextExpensesService(self.user.id, date(2018, 1, 1), date(2018, 4, 1))
        data = service._generate_queryset()

        self.assertEqual(len(data), 3)
        self.assertEqual(data[0].date, date(2018, 1, 1))
        self.assertEqual(data[1].date, date(2018, 2, 1))
        self.assertEqual(data[2].date, date(2018, 3, 1))

    def test_service_gets_correctly_dates(self):
        service = NextExpensesService(self.user.id, date(2018, 1, 1), date(2018, 4, 1))
        self.assertEqual(service._get_dates(), [
            date(2018, 1, 1),
            date(2018, 2, 1),
            date(2018, 3, 1),
            date(2018, 4, 1)
        ])

    def test_returns_transactions_groupped_by_description(self):
        t1 = self.create_transaction(-100, 'shoes', due_date=date(2018, 1, 5))
        t2 = self.create_transaction(-100, 'shoes', due_date=date(2018, 2, 10))
        t3 = self.create_transaction(-100, 'shoes', due_date=date(2018, 3, 15))

        service = NextExpensesService(self.user.id, date(2018, 1, 1), date(2018, 4, 1))
        data = service.generate_data()

        self.assertEqual(len(data), 1)
        self.assertEqual(data[0][date(2018, 1, 1)], [ t1 ])
        self.assertEqual(data[0][date(2018, 2, 1)], [ t2 ])
        self.assertEqual(data[0][date(2018, 3, 1)], [ t3 ])

    def test_returns_transactions_groupped_by_description_as_list(self):
        t1 = self.create_transaction(-100, 'shoes', due_date=date(2018, 1, 5))
        t2 = self.create_transaction(-100, 'shoes', due_date=date(2018, 1, 20))
        t3 = self.create_transaction(-100, 'shoes', due_date=date(2018, 2, 10))
        t4 = self.create_transaction(-100, 'shoes', due_date=date(2018, 3, 15))

        service = NextExpensesService(self.user.id, date(2018, 1, 1), date(2018, 4, 1))
        data = service.generate_data()

        self.assertEqual(len(data), 1)
        self.assertEqual(data[0][date(2018, 1, 1)], [ t1, t2 ])
        self.assertEqual(data[0][date(2018, 2, 1)], [ t3 ])
        self.assertEqual(data[0][date(2018, 3, 1)], [ t4 ])

    def test_returns_several_transactions_groupped_by_description_as_list(self):
        #shoes
        shoes1 = self.create_transaction(-100, 'shoes', due_date=date(2018, 1, 5))
        shoes2 = self.create_transaction(-100, 'shoes', due_date=date(2018, 1, 20))
        shoes3 = self.create_transaction(-100, 'shoes', due_date=date(2018, 2, 10))
        #hat
        hat1 = self.create_transaction(-100, 'hat', due_date=date(2018, 1, 10))
        hat2 = self.create_transaction(-100, 'hat', due_date=date(2018, 4, 5))

        service = NextExpensesService(self.user.id, date(2018, 1, 1), date(2018, 4, 1))
        data = service.generate_data()

        self.assertEqual(len(data), 2)
        self.assertEqual(data[1][date(2018, 1, 1)], [ shoes1, shoes2 ])
        self.assertEqual(data[1][date(2018, 2, 1)], [ shoes3 ])
        self.assertEqual(data[1][date(2018, 3, 1)], [ ])
        self.assertEqual(data[1][date(2018, 4, 1)], [ ])
        self.assertEqual(data[0][date(2018, 1, 1)], [ hat1 ])
        self.assertEqual(data[0][date(2018, 2, 1)], [  ])
        self.assertEqual(data[0][date(2018, 3, 1)], [  ])
        self.assertEqual(data[0][date(2018, 4, 1)], [ hat2 ])