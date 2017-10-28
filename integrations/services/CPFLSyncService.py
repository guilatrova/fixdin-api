import json
import requests
import traceback
from datetime import datetime

from integrations.models import SyncHistory
from integrations.services.SyncService import SyncService
from transactions.models import Transaction, Category, Account

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
    def __init__(self, user, settings):
        super().__init__(user, settings)
        self.cpfl_service = CPFL()

    def run(self, trigger):
        super().run(trigger)

        succeed_count, created, failed_count, errors, result = self._inner_run()

        if succeed_count > 0:
            status = SyncHistory.SUCCESS if failed_count == 0 else SyncHistory.PARTIAL
        else:
            status = SyncHistory.FAIL

        if status == SyncHistory.SUCCESS:
            result = "{} created".format(created)
        elif status == SyncHistory.PARTIAL:
            result = "{} created {} places failed".format(created, failed_count)

        history = SyncHistory.objects.create(
            settings=self.settings[0].settings,
            status=status,
            result=result,
            details=errors,
            trigger=trigger
        )
                
        return history

    def _inner_run(self):
        succeed_count = 0
        failed_count = 0
        created = 0
        errors = ""
        result = ""

        for setting in self.settings:
            try:
                contas = self.cpfl_service.recuperar_contas_abertas(setting.documento, setting.imovel)
                self._save_transactions(contas)
                created += len(contas)
                succeed_count += 1
            except Exception as exc:
                failed_count += 1
                result = str(exc)
                errors += traceback.format_exc() + "\n"

        return succeed_count, created, failed_count, errors, result

    def _format_conta(self, conta):
        return {
            "NumeroContaEnergia": conta["NumeroContaEnergia"],
            "CodigoBarras": conta['CodigoBarras'],
            "DescricaoFatura": conta["DescricaoFatura"],
            "MesReferencia": conta["MesReferencia"],
            "Vencimento": datetime.strptime(conta['Vencimento'], '%Y-%m-%dT%H:%M:%S').date(),
            "Valor": float(conta["Valor"].replace(".", "").replace(",", ".")),
        }

    def _generate_ref_tag(self, conta):
        return conta["NumeroContaEnergia"]

    def _should_create_transaction(self, conta):
        tag = self._generate_ref_tag(conta)
        if Transaction.objects.filter(user=self.user, generic_tag=tag).exists():
            return False
        return True

    def _save_transactions(self, contas):
        contas = [self._format_conta(x) for x in contas if self._should_create_transaction(x)]
        #TODO: Change it to be configurable
        account = Account.objects.filter(user=self.user).first()
        category = Category.objects.filter(user=self.user).first()

        for conta in contas:
            description = conta['DescricaoFatura']
            details = 'Mes Referencia:{} \nCod Barras:{}'.format(conta['MesReferencia'], conta['CodigoBarras'])

            Transaction.objects.create(
                description=description,
                details=details,
                account=account,
                category=category,
                due_date=conta['Vencimento'],
                value=conta['Valor'],
                kind=Transaction.EXPENSE_KIND
            )