from unittest.mock import MagicMock, patch
from django.test import TestCase
from integrations.services.CPFLSyncService import CPFL_SyncService, CPFL
from integrations.models import SyncHistory

class FakeSettings:
    def __init__(self, documento, imovel):
        self.documento = documento
        self.imovel = imovel
        self.settings = 'settings'

class CPFL_SyncServiceTestCase(TestCase):
    def test_invalid_trigger_throws_exceptions(self):
        cpfl_service = CPFL_SyncService(None)
        self.assertRaises(AssertionError, cpfl_service.run, 'Invalid')
    
    @patch.object(CPFL, 'recuperar_contas_abertas', return_value=[0, 1])
    @patch('integrations.models.SyncHistory.objects', return_value=MagicMock())
    def test_asserts_succeed(self, create_mock, recuperar_contas_mock):
        cpfl_service = CPFL_SyncService(
            [MagicMock(documento=x, imovel='imovel', settings='settings') for x in range(1, 4)]
            )
        cpfl_service.run(SyncHistory.MANUAL)

        self.assertEqual(recuperar_contas_mock.call_count, 3)
        create_mock.create.assert_called_once_with(settings='settings', status=SyncHistory.SUCCESS, details="", result='6 created', trigger=SyncHistory.MANUAL)