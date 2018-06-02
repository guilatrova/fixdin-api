from datetime import date

from dateutil import parser
from dateutil.relativedelta import relativedelta
from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.views import APIView

from paymentorders.services import NextExpensesService
from transactions.serializers import TransactionSerializer


class PaymentOrderAPIView(APIView):
    def get(self, request, format='json'):
        data = self._get_transactions()
        return Response(data)

    def _get_transactions(self):
        service = NextExpensesService(
            self.request.user.id,
            self._get_from_date(),
            self._get_until_date()
        )
        raw = service.generate_data()
        return self._serialize_data(raw)

    def _serialize_data(self, data):
        for group in data:
            for date_group in group:
                group[date_group] = [ TransactionSerializer(x).data for x in group[date_group] ]

        return data

    def _get_from_date(self):
        if 'from' in self.request.query_params:
            return parser.parse(self.request.query_params['from']).date()
        return date.today()

    def _get_until_date(self):
        if 'until' in self.request.query_params:
            return parser.parse(self.request.query_params['until']).date()
        return date.today() + relativedelta(months=1)
