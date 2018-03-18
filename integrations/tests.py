from datetime import datetime, date
from decimal import Decimal
from unittest.mock import MagicMock, patch
from django.urls import reverse, resolve
from django.test import TestCase
from rest_framework.test import APITestCase, APIRequestFactory, force_authenticate
from rest_framework import status

from transactions.models import Transaction
from transactions.tests.base_test import BaseTestHelper
from integrations.services.CPFLSyncService import CPFL_SyncService, CPFL
from integrations.models import SyncHistory, IntegrationSettings, Integration, CPFL_Settings
from integrations.serializers import ServiceSettingsSerializer
from integrations import views
from common.tests_helpers import UrlsTestHelper

CONTAS_RECUPERADAS_MOCK = [
    {
        "NumeroContaEnergia": "1",
        "CodigoBarras": "[CODBARRA]",
        "DescricaoFatura": "Descricao",
        "MesReferencia": "[MESREF]",
        "Vencimento": "2017-10-01T00:00:00",
        "Valor": "1.207,58",
    },
    {
        "NumeroContaEnergia": "2",
        "CodigoBarras": "[CODBARRA]",
        "DescricaoFatura": "Descricao",
        "MesReferencia": "[MESREF]",
        "Vencimento": "2017-10-01T00:00:00",
        "Valor": "1.207,58"
    }
]

class CPFL_SyncServiceTestCase(TestCase):
    def setUp(self):
        self.user_mock = MagicMock()
        self.mocked_settings = [MagicMock(documento=x, imovel='imovel' + str(x), settings='settings') for x in range(1, 3)]
        self.cpfl_sync_service = CPFL_SyncService(self.user_mock, self.mocked_settings)

        self.create_transaction_mock_patcher = patch('transactions.models.Transaction.objects.create')
        self.create_history_mock_patcher = patch('integrations.models.SyncHistory.objects.create')

        self.create_transaction_mock = self.create_transaction_mock_patcher.start()
        self.create_history_mock = self.create_history_mock_patcher.start()

    def tearDown(self):
        self.create_transaction_mock_patcher.stop()
        self.create_history_mock_patcher.stop()

    def test_invalid_trigger_throws_exceptions(self):
        self.assertRaises(AssertionError, self.cpfl_sync_service.run, 'Invalid')

    @patch.object(CPFL, '_gerar_token', return_value=('token', { 'info': 'info' }))
    def test_validate_settings_successful(self, gerar_token_mock):
        result, message = self.cpfl_sync_service.validate_settings()

        self.assertTrue(result)
        self.assertFalse(message)

    @patch.object(CPFL, '_gerar_token', side_effect=Exception("error"))
    def test_validate_settings_failed(self, gerar_token_mock):
        result, message = self.cpfl_sync_service.validate_settings()

        self.assertFalse(result)
        self.assertIn('imovel1', message)
        self.assertIn('imovel2', message)
    
    @patch.object(CPFL_SyncService, '_save_transactions', return_value=2)
    @patch.object(CPFL_SyncService, '_should_create_transaction', return_value=True)
    @patch.object(CPFL, 'recuperar_contas_abertas', return_value=CONTAS_RECUPERADAS_MOCK)
    def test_asserts_inner_run_succeed(self, recuperar_contas_mock, should_create_mock, save_transactions_mock):
        succeed, created, failed, errors, result = self.cpfl_sync_service._inner_run()

        self.assertEqual(recuperar_contas_mock.call_count, 2)
        self.assertEqual(save_transactions_mock.call_count, 2)        
        self.assertEqual(succeed, 2)
        self.assertEqual(created, 4)
        self.assertFalse(errors)
        self.assertFalse(result)

    @patch.object(CPFL, 'recuperar_contas_abertas', side_effect=Exception('Something went wrong'))
    def test_asserts_inner_run_failed(self,recuperar_contas_mock):
        error_message = 'Something went wrong'

        succeed, created, failed, errors, result = self.cpfl_sync_service._inner_run()

        self.assertEqual(recuperar_contas_mock.call_count, 2)
        self.assertFalse(self.create_transaction_mock.called)
        self.assertEqual(succeed, 0)
        self.assertEqual(created, 0)
        self.assertIn(error_message, errors)
        self.assertIn(error_message, result)

    @patch.object(CPFL_SyncService, '_save_transactions', return_value=2)
    @patch.object(CPFL_SyncService, '_should_create_transaction', return_value=True)
    @patch.object(CPFL, 'recuperar_contas_abertas', side_effect=[CONTAS_RECUPERADAS_MOCK, Exception('Something went wrong')])
    def test_asserts_inner_run_partial(self, recuperar_contas_mock, should_create_mock, save_transactions_mock):
        error_message = 'Something went wrong'

        succeed, created, failed, errors, result = self.cpfl_sync_service._inner_run()

        self.assertEqual(recuperar_contas_mock.call_count, 2)
        self.assertTrue(save_transactions_mock.called)
        self.assertEqual(succeed, 1)
        self.assertEqual(created, 2)
        self.assertEqual(failed, 1)
        self.assertIn(error_message, errors)
        self.assertIn(error_message, result)

    @patch.object(CPFL_SyncService, '_inner_run', return_value=(1, 3, 0, "", ""))
    def test_run_creates_successful_history(self, inner_run_mock):
        self.cpfl_sync_service.run(SyncHistory.MANUAL)

        self.create_history_mock.assert_called_once_with(
            settings='settings',
            status=SyncHistory.SUCCESS,
            result="3 created",
            details="",
            trigger=SyncHistory.MANUAL,
        )

    @patch.object(CPFL_SyncService, '_inner_run', return_value=(0, 0, 2, 
        "Long stack trace that explains that Something went wrong", "Something went wrong"))
    def test_run_creates_failed_history(self, inner_run_mock):
        self.cpfl_sync_service.run(SyncHistory.MANUAL)

        self.create_history_mock.assert_called_once_with(
            settings='settings',
            status=SyncHistory.FAIL,
            result="Something went wrong",
            details="Long stack trace that explains that Something went wrong",
            trigger=SyncHistory.MANUAL,
        )

    @patch.object(CPFL_SyncService, '_inner_run', return_value=(1, 3, 2, 
        "Long stack trace that explains that Something went wrong", "Something went wrong"))
    def test_run_creates_partial_succeed_history(self, inner_run_mock):
        self.cpfl_sync_service.run(SyncHistory.AUTO)

        self.create_history_mock.assert_called_once_with(
            settings='settings',
            status=SyncHistory.PARTIAL,
            result="3 created 2 places failed",
            details="Long stack trace that explains that Something went wrong",
            trigger=SyncHistory.AUTO,
        )

    def test_should_create_transaction(self):
        def filter_side_effect(**kwargs):
            mock = MagicMock()            
            mock.exists.return_value = (kwargs['generic_tag'] == '1')

            return mock

        with patch('transactions.models.Transaction.objects.filter', side_effect=filter_side_effect) as mock:
            self.assertFalse(self.cpfl_sync_service._should_create_transaction(CONTAS_RECUPERADAS_MOCK[0]))
            mock.assert_called_once_with(account__user=self.user_mock, generic_tag='1')

            self.assertTrue(self.cpfl_sync_service._should_create_transaction(CONTAS_RECUPERADAS_MOCK[1]))
            self.assertEqual(mock.call_count, 2)
            mock.assert_called_with(account__user=self.user_mock, generic_tag='2')
    
    @patch('transactions.models.Account.objects.filter')
    @patch('transactions.models.Category.objects.filter')
    @patch.object(CPFL_SyncService, '_should_create_transaction', return_value=True)
    @patch.object(CPFL_SyncService, '_generate_ref_tag', return_value='TAG')
    def test_save_transactions(self, tag_mock, should_create_mock, category_filter_mock, account_filter_mock):
        mock = self.create_transaction_mock
        conta = CONTAS_RECUPERADAS_MOCK[1]

        self.cpfl_sync_service._save_transactions([conta])

        category_filter_mock.assert_called_once_with(user=self.user_mock, kind=Transaction.EXPENSE_KIND)
        account_filter_mock.assert_called_once_with(user=self.user_mock)

        mock.assert_called_once()
        mock.assert_called_with(
            description='Descricao',
            details='Mes Referencia:{} \nCod Barras:{}'.format(conta['MesReferencia'], conta['CodigoBarras']),
            account=account_filter_mock().first(),
            category=category_filter_mock().first(),
            due_date=datetime(2017, 10, 1, 0, 0).date(),
            value=Decimal('1207.58'),
            kind=Transaction.EXPENSE_KIND,
            generic_tag="TAG"
        )
        
class CPFL_SyncServiceIntegrationTestCase(TestCase, BaseTestHelper):
    def setUp(self):
        self.user, token = self.create_user('testuser', email='testuser@test.com', password='testing')
        self.create_category(name="luz", kind=Transaction.EXPENSE_KIND)
        self.settings = [self.create_integration()]

    def create_integration(self):
        integration = Integration.objects.get(name_id="cpfl") #Already created in migrations
        base_settings = IntegrationSettings.objects.create(integration=integration, user=self.user)
        cpfl_settings = CPFL_Settings.objects.create(settings=base_settings, name="Home", documento="05717538847", imovel="4001647780")

        return cpfl_settings

    @patch.object(CPFL, 'recuperar_contas_abertas', return_value=CONTAS_RECUPERADAS_MOCK)
    def test_create_transactions_from_cpfl(self, recuperar_contas_mock):
        service = CPFL_SyncService(self.user, self.settings)
        
        history_result, created = service.run(SyncHistory.AUTO)        

        self.assertEqual(SyncHistory.objects.all().count(), 1)
        self.assertEqual(Transaction.objects.all().count(), 2)
        self.assertEqual(history_result.status, SyncHistory.SUCCESS)
        self.assertEqual(created, 2)

class IntegrationsUrlsTestCase(TestCase, UrlsTestHelper):

    def test_resolves_list_url(self):
        resolver = self.resolve_by_name('integrations')

        self.assertEqual(resolver.func.cls, views.ListIntegrationsAPIView)

    def test_resolves_service_name_url(self):
        resolver = self.resolve_by_name('integrations-service', name_id="cpfl")

        self.assertEqual(resolver.func.cls, views.IntegrationSettingsAPIView)

    def test_resolves_list_history_service_url(self):
        resolver = self.resolve_by_name('integrations-service-histories', name_id="cpfl")

        self.assertEqual(resolver.func.cls, views.ListIntegrationServiceHistoryAPIView)

class IntegrationsViewsTestCase(TestCase):

    def test_list_integrations_allows_only_get(self):
        view = views.ListIntegrationsAPIView()

        self.assertEqual(['GET', 'OPTIONS'], view.allowed_methods)

    def test_list_integration_history_filters_by_user_and_service(self):
        request_mock = MagicMock()        
        view = views.ListIntegrationServiceHistoryAPIView(request=request_mock, kwargs={'name_id':"cpfl"})

        with patch('integrations.models.SyncHistory.objects.filter') as mock:
            view.get_queryset()

            mock.assert_called_once_with(
                settings__user=request_mock.user,
                settings__integration__name_id='cpfl'
            )

    def test_list_integrations_history_allows_only_get(self):
        view = views.ListIntegrationServiceHistoryAPIView()

        self.assertEqual(['GET', 'OPTIONS'], view.allowed_methods)

class IntegrationsAPITestCase(APITestCase, BaseTestHelper):
    def setUp(self):
        self.user, token = self.create_user('testuser', email='testuser@test.com', password='testing')
        self.client = self.create_authenticated_client(token)
        self.settings = IntegrationSettings.objects.create(integration=Integration.objects.get(name_id='cpfl'), user=self.user)

    def test_retrieves_services_list(self):
        response = self.client.get(reverse('integrations'))

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual('CPFL', response.data[0]['name'])

    def test_retrieves_service_history(self):
        SyncHistory.objects.create(settings=self.settings, status=SyncHistory.SUCCESS, result='good', details="", trigger=SyncHistory.MANUAL)

        response = self.client.get(self.get_url('integrations-service-histories', name_id='cpfl'))

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(len(response.data), 1)

    def test_get_integration_service_settings(self):
        CPFL_Settings.objects.create(settings=self.settings, name="local1", documento='11', imovel='12')
        CPFL_Settings.objects.create(settings=self.settings, name="local2", documento='11', imovel='13')

        response = self.client.get(self.get_url('integrations-service', name_id='cpfl'))

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(len(response.data['cpfl_settings']), 2)

    def test_put_integration_service_settings(self):
        cpfl_setting = CPFL_Settings.objects.create(settings=self.settings, name="local1", documento='11', imovel='12')
        payload = {
            'enabled': True,
            'cpfl_settings': [
                { 'id': cpfl_setting.id, 'name': cpfl_setting.name, 'documento': cpfl_setting.documento, 'imovel': cpfl_setting.imovel },
                { 'name': 'new', 'documento': '2', 'imovel': 'im-novo' }
            ]
        }

        response = self.client.put(self.get_url('integrations-service', name_id='cpfl'), payload, format='json')

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(len(response.data['cpfl_settings']), 2)
        self.assertEqual(CPFL_Settings.objects.count(), 2)

    def test_post_integration_settings_runs_it(self):
        history = SyncHistory.objects.create(settings=self.settings, status=SyncHistory.SUCCESS, result='good', details="", trigger=SyncHistory.MANUAL)

        with patch('integrations.services.CPFLSyncService.CPFL_SyncService.run', return_value=(history, 2)) as mock:
            response = self.client.post(self.get_url('integrations-service', name_id='cpfl'), format='json')

            self.assertEqual(status.HTTP_201_CREATED, response.status_code)
            self.assertEqual(history.id, response.data['id'])
            mock.assert_called_once_with(SyncHistory.MANUAL)

    def test_post_integration_settings_failed(self):
        history = SyncHistory.objects.create(settings=self.settings, status=SyncHistory.FAIL, result='bad', details="", trigger=SyncHistory.MANUAL)

        with patch('integrations.services.CPFLSyncService.CPFL_SyncService.run', return_value=(history, 2)) as mock:
            response = self.client.post(self.get_url('integrations-service', name_id='cpfl'), format='json')

            self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
            self.assertEqual(history.id, response.data['id'])
            mock.assert_called_once_with(SyncHistory.MANUAL)

    def test_post_integration_settings_no_creations(self):
        history = SyncHistory.objects.create(settings=self.settings, status=SyncHistory.SUCCESS, result='good', details="", trigger=SyncHistory.MANUAL)

        with patch('integrations.services.CPFLSyncService.CPFL_SyncService.run', return_value=(history, 0)) as mock:
            response = self.client.post(self.get_url('integrations-service', name_id='cpfl'), format='json')

            self.assertEqual(status.HTTP_200_OK, response.status_code)
            self.assertEqual(history.id, response.data['id'])
            mock.assert_called_once_with(SyncHistory.MANUAL)
        
    def get_url(self, name, **kwargs):
        return reverse(name, kwargs=kwargs)

class IntegrationsSerializersTestCase(TestCase):
    def test_valid_cpfl_serializer_without_base_settings(self):
        data = {
            'last_sync': None,
            'status': None,
            'enabled': False,
            'cpfl_settings': [
                { 'name': 'place1', 'documento': '1', 'imovel': 'im1' },
                { 'name': 'place2', 'documento': '2', 'imovel': 'im2' },
            ]
        }

        serializer = ServiceSettingsSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_valid_complete_cpfl_serializer(self):
        data = {
            'last_sync': date(2017, 10, 1),
            'status': IntegrationSettings.SUCCESS,
            'enabled': True,
            'cpfl_settings': [
                { 'name': 'place1', 'documento': '1', 'imovel': 'im1' },
                { 'name': 'place2', 'documento': '2', 'imovel': 'im2' },
            ]
        }

        serializer = ServiceSettingsSerializer(data=data)
        self.assertTrue(serializer.is_valid())