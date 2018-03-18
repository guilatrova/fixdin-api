from unittest import mock
import datetime
from unittest import skip
from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse, resolve
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework.authtoken.models import Token
from transactions.models import *

class BaseTestHelperFactory:
    """
    Created to be used on setupTestData and be faster. When possible old BaseTestHelper will be extinguished.
    """

    @classmethod
    def create_transaction(cls, value=None, description='description', kind=None, account=None, category=None, 
                            due_date=datetime.datetime.today(), payment_date=None, priority=0, deadline=10):
        if value is None:
            value = cls.value

        if account is None:
            account = cls.account

        if category is None:
            category = cls.category

        if kind is None:
            kind = Transaction.EXPENSE_KIND if value <= 0 else Transaction.INCOME_KIND    

        transaction = Transaction.objects.create(
            account=account,
            due_date=due_date,
            description=description,
            category=category,
            value=value,
            kind=kind,
            payment_date=payment_date,
            priority=priority,
            deadline=deadline
            )

        return transaction

    @classmethod
    def create_account(cls, user=None, name='default', current_effective_balance=0, current_real_balance=0):
        if user is None:
            user = cls.user

        return Account.objects.create(name=name, user=user, current_effective_balance=current_effective_balance, current_real_balance=current_real_balance)

    @classmethod
    def create_user(cls, name='testuser', **kwargs):
        user = User.objects.create_user(kwargs)
        token = Token.objects.get(user=user)

        return user, token

    @classmethod
    def create_category(cls, name, user=None, kind=Category.EXPENSE_KIND):
        if user is None:
            user = cls.user

        return Category.objects.create(kind=kind, user=user, name=name)

    @classmethod
    def create_authenticated_client(cls, token):
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        return client
        
class BaseTestHelper:
    '''
    Class used to create some resources to backup tests
    '''
    def create_transaction(self, value=None, description='description', kind=None, account=None, category=None, 
                            due_date=datetime.datetime.today(), payment_date=None, priority=0, deadline=10):
        if value is None:
            value = self.value

        if account is None:
            account = self.account

        if category is None:
            category = self.category

        if kind is None:
            kind = Transaction.EXPENSE_KIND if value <= 0 else Transaction.INCOME_KIND    

        transaction = Transaction.objects.create(
            account=account,
            due_date=due_date,
            description=description,
            category=category,
            value=value,
            kind=kind,
            payment_date=payment_date,
            priority=priority,
            deadline=deadline
            )

        return transaction

    def create_account(self, user=None, name='default', current_effective_balance=0, current_real_balance=0):
        if user is None:
            user = self.user

        return Account.objects.create(name=name, user=user, current_effective_balance=current_effective_balance, current_real_balance=current_real_balance)

    def create_user(self, name='testuser', **kwargs):
        user = User.objects.create_user(kwargs)
        token = Token.objects.get(user=user)

        return user, token

    def create_category(self, name, user=None, kind=Category.EXPENSE_KIND):
        if user is None:
            user = self.user

        return Category.objects.create(kind=kind, user=user, name=name)

    def create_authenticated_client(self, token):
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        return client

