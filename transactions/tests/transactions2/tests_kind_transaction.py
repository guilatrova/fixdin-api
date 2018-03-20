import datetime
from unittest import mock, skip
from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework.authtoken.models import Token
from transactions.models import *
from transactions import views
from transactions.factories import create_periodic_transactions, create_transfer_between_accounts
from common.tests_helpers import UrlsTestHelper

class KindTransactionUrlTest(TestCase, UrlsTestHelper):

    def test_resolves_list_url(self):
        resolver = self.resolve_by_name('kind_transactions')
        self.assertEqual(resolver.func.cls, views.TransactionViewSet)

    def test_resolves_single_url(self):
        resolver = self.resolve_by_name('kind_transaction', pk=1)
        self.assertEqual(resolver.func.cls, views.TransactionViewSet)

    def test_resolves_list_to_actions(self):
        resolver = self.resolve_by_name('kind_transactions')
        self.assert_resolves_actions(resolver, { 
            'get': 'list',
            'post': 'create',
            'delete': 'destroy_all_periodics',
            'patch': 'patch_list'
        })
        
    def test_list_url_allows_actions(self):
        resolver = self.resolve_by_name('kind_transactions')
        self.assert_has_actions(['get', 'post', 'delete', 'patch'], resolver.func.actions)

    def test_single_url_allows_actions(self):
        resolver = self.resolve_by_name('kind_transaction', pk=1)
        self.assert_has_actions(['get', 'put', 'delete', 'patch'], resolver.func.actions)

