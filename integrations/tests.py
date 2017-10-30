from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch
from unittest import skip
from django.test import TestCase
from integrations.services.CPFLSyncService import CPFL_SyncService, CPFL
from integrations.models import SyncHistory, IntegrationSettings, Integration, CPFL_Settings
from transactions.models import Transaction
from transactions.tests.base_test import BaseTestHelper

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
    
    @patch.object(CPFL_SyncService, '_save_transactions', return_value=True)
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

    @patch.object(CPFL_SyncService, '_save_transactions', return_value=True)
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
    def test_save_transactions(self, should_create_mock, category_filter_mock, account_filter_mock):
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
            kind=Transaction.EXPENSE_KIND
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
        
        history_result = service.run(SyncHistory.AUTO)        

        self.assertEqual(SyncHistory.objects.all().count(), 1)
        self.assertEqual(Transaction.objects.all().count(), 2)
        self.assertEqual(history_result.status, SyncHistory.SUCCESS)