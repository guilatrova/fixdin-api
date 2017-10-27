from datetime import datetime
from unittest.mock import MagicMock, patch
from django.test import TestCase
from integrations.services.CPFLSyncService import CPFL_SyncService, CPFL
from integrations.models import SyncHistory

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
        self.mocked_settings = [MagicMock(documento=x, imovel='imovel', settings='settings') for x in range(1, 3)]
        self.cpfl_sync_service = CPFL_SyncService(self.user_mock, self.mocked_settings)

        self.create_transaction_mock_patcher = patch('transactions.models.Transaction.objects.create')
        self.create_history_mock_patcher = patch('integrations.models.SyncHistory.objects.create')

        self.create_transaction_mock = self.create_transaction_mock_patcher.start()
        self.create_history_mock_patcher = self.create_history_mock_patcher.start()

    def tearDown(self):
        self.create_transaction_mock_patcher.stop()
        self.create_history_mock_patcher.stop()

    def test_invalid_trigger_throws_exceptions(self):
        self.assertRaises(AssertionError, self.cpfl_sync_service.run, 'Invalid')
    
    @patch.object(CPFL, 'recuperar_contas_abertas', return_value=CONTAS_RECUPERADAS_MOCK)
    def test_asserts_inner_run_succeed(self, recuperar_contas_mock):
        succeed, created, failed, errors, result = self.cpfl_sync_service._inner_run()

        self.assertEqual(recuperar_contas_mock.call_count, 2)
        self.assertEqual(self.create_transaction_mock.call_count, 4)
        self.assertEqual(succeed, 2)
        self.assertEqual(created, 4)
        self.assertFalse(errors)
        self.assertFalse(result)
        # create_transaction_mock.assert_called_with(a=recuperar_contas_mock.return_value[0]['a'])
        # create_history_mock.assert_called_once_with(settings='settings', status=SyncHistory.SUCCESS, details="", result='6 created', trigger=SyncHistory.MANUAL)

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

    @patch.object(CPFL, 'recuperar_contas_abertas', side_effect=[CONTAS_RECUPERADAS_MOCK, Exception('Something went wrong')])
    def test_asserts_inner_run_partial(self, recuperar_contas_mock):
        error_message = 'Something went wrong'

        succeed, created, failed, errors, result = self.cpfl_sync_service._inner_run()

        self.assertEqual(recuperar_contas_mock.call_count, 2)
        self.assertEqual(self.create_transaction_mock.call_count, 2)
        self.assertEqual(succeed, 1)
        self.assertEqual(created, 2)
        self.assertEqual(failed, 1)
        self.assertIn(error_message, errors)
        self.assertIn(error_message, result)