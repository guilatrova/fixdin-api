from django.shortcuts import render
from datetime import date
from dateutil.relativedelta import relativedelta
from dateutil import parser
from rest_framework.views import APIView
from rest_framework.response import Response
from paymentorders.services import NextExpensesService

class PaymentOrderAPIView(APIView):
    def get(self, request, format='json'):        
        service = NextExpensesService(
            self.request.user.id,
            self._get_from_date(),
            self._get_until_date()
        )
        data = service.generate_data()
        return Response({ 'transactions': data })

    def _get_from_date(self):
        if 'from' in self.request.query_params:
            return parser.parse(self.request.query_params['from']).date()
        return date.today()

    def _get_until_date(self):
        if 'until' in self.request.query_params:
            return parser.parse(self.request.query_params['until']).date()
        return date.today() + relativedelta(months=1)

