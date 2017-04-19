from unittest import mock, skip
from django.test import TestCase
from django.core.urlresolvers import reverse, get_resolver
from django.contrib.auth.models import User
from django.contrib.auth.hashers import check_password
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework_expiring_authtoken.models import ExpiringToken
from fixdin.settings.base import EXPIRING_TOKEN_LIFESPAN

import datetime

class UsersTests(APITestCase):

    def test_register_user(self):
        user_dto = {
            'username': 'guilherme',
            'password': 'abc123456',
            'email': 'guilherme@email.com',
            'first_name': 'Guilherme',
            'last_name': 'Latrova'
        }

        response = self.client.post(reverse('users'), user_dto, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)

    def test_successful_login_returns_token(self):
        user = self.create_user(email='gui@latrova.com', password='abc123456')

        login_dto = {
            'email': 'gui@latrova.com',
            'password': 'abc123456'
        }

        response = self.client.post(reverse('login'), login_dto, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue('token' in response.data)

    def test_token_expires_after_90(self):
        user = self.create_user(email='guilhermelatrova@hotmail.com', password='abc123456')        
        
        expired_token = ExpiringToken.objects.get(user=user)
        expired_token.created -= datetime.timedelta(days=90)
        expired_token.save()
        
        self.assertTrue(expired_token.expired())
    
    def test_should_deny_expired_tokens(self):
        user = self.create_user(email='guilhermelatrova@hotmail.com', password='abc123456')        
        
        expired_token = Token.objects.get(user=user)
        expired_token.created -= EXPIRING_TOKEN_LIFESPAN
        expired_token.save()
        
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + expired_token.key)

        response = self.client.get(reverse('expense-categories'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def create_user(self, name='testuser', **kwargs):
        user = User.objects.create_user(name, **kwargs)
        user.save()

        return user