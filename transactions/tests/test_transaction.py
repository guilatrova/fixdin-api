from unittest import skip
from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework.authtoken.models import Token
from transactions.models import Category, Transaction

class TransactionTestCase(APITestCase):

    def setUp(self):
        self.user, token = self.create_user('testuser', email='testuser@test.com', password='testing')

        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        self.category = self.create_category('car')

    def test_create_expense(self):
        transaction_dto = {
            'due_date': '2017-04-13',
            'description': 'gas',
            'category': self.category.id,
            'value': 40,
            'payed': False,
            'details': ''
        }

        response = self.client.post(reverse('expenses'), transaction_dto, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Transaction.objects.count(), 1)

    #def test_create_

    def create_user(self, name='testuser', **kwargs):
        user = User.objects.create_user(kwargs)
        user.save()        

        return user, user.token

    def create_category(self, name, user=None, kind=Category.EXPENSE_KIND):
        if user is None:
            user = self.user

        category = Category.objects.create(kind=kind, user=user, name=name)
        category.save()
        return category