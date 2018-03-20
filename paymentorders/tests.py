from django.test import TestCase
from django.urls import reverse
from datetime import date
from unittest import skip
from unittest.mock import patch, MagicMock
from rest_framework import status
from transactions.tests.base_test import BaseTestHelperFactory
from paymentorders.services import NextExpensesService
from paymentorders.views import PaymentOrderAPIView
from common.tests_helpers import UrlsTestHelper

class PaymentOrderUrlTestCase(TestCase, UrlsTestHelper):
    def test_resolves_get_url(self):
        resolver = self.resolve_by_name('payment-orders')        
        self.assertEqual(resolver.func.cls, PaymentOrderAPIView)

class PaymentOrderApiTestCase(TestCase, BaseTestHelperFactory):

    @classmethod
    def setUpTestData(cls):
        cls.user, cls.token = cls.create_user(email='testuser@test.com', password='testing')

    def setUp(self):
        self.client = self.create_authenticated_client(self.token)
    
    @patch('paymentorders.views.PaymentOrderAPIView._get_transactions', return_value=[])
    def test_api_get_replies_empty_array(self, mock):        
        response = self.client.get(reverse('payment-orders'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])
    
    @patch('paymentorders.views.PaymentOrderAPIView._get_transactions', return_value=[ { 'id': 1},  { 'id': 2}])
    def test_api_get_replies_array(self, mock):
        response = self.client.get(reverse('payment-orders'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [ {'id':1}, {'id':2} ])
        
class PaymentOrderViewsTestCase(TestCase, BaseTestHelperFactory):

    def setUp(self):
        self.user = MagicMock(id=5)
    
    @patch('paymentorders.views.NextExpensesService', return_value=MagicMock())    
    def test_creates_service_correctly_with_params(self, service_mock):        
        view, request = self.create_view_with_request({'from':'2018-01-01', 'until':'2018-02-01'})
        
        view.get(request)

        service_mock.assert_called_with(self.user.id, date(2018, 1, 1), date(2018, 2, 1))

    @patch('paymentorders.views.date', side_effect=lambda *args, **kw: date(*args, **kw))
    @patch('paymentorders.views.NextExpensesService', return_value=MagicMock())
    def test_creates_service_correctly_without_params(self, service_mock, date_mock):
        date_mock.today.return_value = date(2017, 1, 5)
        view, request = self.create_view_with_request()
        
        view.get(request)

        service_mock.assert_called_with(self.user.id, date(2017, 1, 5), date(2017, 2, 5))

    def create_view_with_request(self, query_params={}):
        mock_request = MagicMock(self.user, user=self.user, query_params=query_params)
        return PaymentOrderAPIView(request=mock_request), mock_request

class NextExpensesServiceTestCase(TestCase, BaseTestHelperFactory):

    @classmethod
    def setUpTestData(cls):
        cls.user, token = cls.create_user(email='testuser@test.com', password='testing')
        cls.category = cls.create_category('category')
        cls.account = cls.create_account()

        cls.other_user, other_user_token = cls.create_user('other', email='other@test.com', password='other')
        cls.other_category = cls.create_category('other', user=cls.other_user)
        cls.other_account = cls.create_account(cls.other_user)

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
        service = NextExpensesService(self.user.id, date(2018, 1, 30), date(2018, 4, 1))
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
        self.assertEqual(data[0]['2018-01-01'], [ t1 ])
        self.assertEqual(data[0]['2018-02-01'], [ t2 ])
        self.assertEqual(data[0]['2018-03-01'], [ t3 ])

    def test_returns_transactions_groupped_by_description_as_list(self):
        t1 = self.create_transaction(-100, 'shoes', due_date=date(2018, 1, 5))
        t2 = self.create_transaction(-100, 'shoes', due_date=date(2018, 1, 20))
        t3 = self.create_transaction(-100, 'shoes', due_date=date(2018, 2, 10))
        t4 = self.create_transaction(-100, 'shoes', due_date=date(2018, 3, 15))

        service = NextExpensesService(self.user.id, date(2018, 1, 1), date(2018, 4, 1))
        data = service.generate_data()

        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['2018-01-01'], [ t1, t2 ])
        self.assertEqual(data[0]['2018-02-01'], [ t3 ])
        self.assertEqual(data[0]['2018-03-01'], [ t4 ])

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
        self.assertEqual(data[1]['2018-01-01'], [ shoes1, shoes2 ])
        self.assertEqual(data[1]['2018-02-01'], [ shoes3 ])
        self.assertEqual(data[1]['2018-03-01'], [ ])
        self.assertEqual(data[1]['2018-04-01'], [ ])
        self.assertEqual(data[0]['2018-01-01'], [ hat1 ])
        self.assertEqual(data[0]['2018-02-01'], [  ])
        self.assertEqual(data[0]['2018-03-01'], [  ])
        self.assertEqual(data[0]['2018-04-01'], [ hat2 ])