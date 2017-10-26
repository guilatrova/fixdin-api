import json
import requests
import traceback

from integrations.models import SyncHistory
from integrations.services.SyncService import SyncService
from transactions.models import Transaction

TOKEN_URL = 'https://servicosonline.cpfl.com.br/agencia-webapi/api/token'
SITUACAO_URL = 'https://servicosonline.cpfl.com.br/agencia-webapi/api/historico-contas/validar-situacao'

INFO_KEYS = [
    'CodigoFase', 'IndGrupoA', 'Situacao', 'CodClasse', 
    'CodEmpresaSAP', 'CodigoTipoParceiro', 'ParceiroNegocio']

class CPFL:
    def _gerar_token(self, documento, nr_instalacao):
        payload = {
            'client_id': 'agencia-virtual-cpfl-web',
            'grant_type': 'instalacao',
            'numero_documento': documento,
            'numero_instalacao': nr_instalacao
        }

        resp = requests.post(TOKEN_URL, payload)
        if resp.ok:
            dic = resp.json()
            token = dic.get('access_token')
            instalacao = json.loads(dic.get('Instalacao'))

            info = dict([(k, v) for k, v in instalacao.items() if k in INFO_KEYS])
            info['CodigoClasse'] = info.pop('CodClasse')
            return token, info

        raise Exception(resp.json().get('error'))

    def _obter_contas_aberto(self, token, instalacao, **kwargs):
        payload = {
            "RetornarDetalhes": True,
            "GerarProtocolo": False,
            "Instalacao": instalacao,
        }
        payload.update(kwargs)
        assert len(payload) == 10

        headers = {
            'Authorization': 'Bearer {}'.format(token)
        }
        resp = requests.post(SITUACAO_URL, payload, headers=headers)

        if resp.ok:
            return resp.json().get('ContasAberto', [])

        raise Exception(resp.json().get('error'))

    def recuperar_contas_abertas(self, documento, instalacao):
        """Autentica e recupera todas as contas em aberta do documento e instalacao"""
        token, info = self._gerar_token(documento, instalacao)
        contas = self._obter_contas_aberto(token, instalacao, **info)
        return contas

class CPFL_SyncService(SyncService):
    def __init__(self, settings):
        super().__init__(settings)
        self.cpfl_service = CPFL()

    def run(self, trigger):
        super().run(trigger)
        succeed_count = 0
        failed_count = 0
        created = 0
        errors = ""

        for setting in self.settings:
            try:
                contas = self.cpfl_service.recuperar_contas_abertas(setting.documento, setting.imovel)
                # self._save_transactions(contas)
                created += len(contas)
                succeed_count += 1
            except Exception as exc:
                failed_count += 1
                result = str(exc)
                errors += traceback.format_exc() + "\n"

        if succeed_count > 0:
            status = SyncHistory.SUCCESS if failed_count == 0 else SyncHistory.PARTIAL
        else:
            status = SyncHistory.FAIL

        if status == SyncHistory.SUCCESS:
            result = "{} created".format(created)
        elif status == SyncHistory.PARTIAL:
            result = "{} created {} places failed".format(created, failed_count)

        history = SyncHistory.objects.create(settings=self.settings[0].settings,
                                            status=status,
                                            result=result,
                                            details=errors,
                                            trigger=trigger)
                
        return history

    def _save_transactions(self, contas):
        Transaction.objects.create()