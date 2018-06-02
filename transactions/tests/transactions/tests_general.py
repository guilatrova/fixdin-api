from datetime import date
from unittest import mock, skip

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from common.tests_helpers import SerializerTestHelper, UrlsTestHelper
from transactions import views
from transactions.models import HasKind, Transaction
from transactions.serializers import TransactionSerializer
from transactions.tests.base_test import BaseTestHelperFactory, OtherUserDataTestSetupMixin, UserDataTestSetupMixin


class TransactionManagerTestCase(UserDataTestSetupMixin, TestCase, BaseTestHelperFactory):    
    def test_delete_single(self):
        t = self.create_transaction(-100)
        t.delete()
        self.assertFalse(Transaction.objects.filter(pk=t.id).exists())

    @skip('unfinished')
    def test_delete_list_without_consent_param(self):
        pass

    @skip('unfinished')
    def test_delete_list_with_consent(self):
        pass

class TransactionUrlTestCase(UrlsTestHelper, TestCase):
    
    def test_resolves_list_url(self):
        resolver = self.resolve_by_name('transactions')
        self.assertEqual(resolver.func.cls, views.TransactionViewSet)

    def test_resolves_single_url(self):
        resolver = self.resolve_by_name('transaction', pk=1)
        self.assertEqual(resolver.func.cls, views.TransactionViewSet)

    def test_resolves_list_to_actions(self):
        resolver = self.resolve_by_name('transactions')
        self.assert_resolves_actions(resolver, {
            'get': 'list',
            'post': 'create',
            'delete': 'destroy_all_periodics',
            'patch': 'partial_update_list'
        })

    def test_list_url_allows_actions(self):
        resolver = self.resolve_by_name('transactions')
        self.assert_has_actions(['get', 'post', 'delete', 'patch'], resolver.func.actions)

    def test_single_url_allows_actions(self):
        resolver = self.resolve_by_name('transaction', pk=1)
        self.assert_has_actions(['get', 'put', 'delete', 'patch'], resolver.func.actions)

    def test_resolves_oldest_pending_expense_url(self):
        resolver = self.resolve_by_name('oldest-pending-expense')
        self.assertEqual(resolver.func.cls, views.OldestPendingExpenseAPIView)
