from datetime import datetime
from django.db.models import Sum
from rest_framework.views import APIView
from rest_framework.response import Response
from transactions.models import Category, Transaction, Account

class BalanceAPIView(APIView):

    def get(self, request, format='json'):
        additional_filters = self.get_filter()
        total_sum = Transaction.objects\
            .filter(account__user_id=request.user.id, **additional_filters)\
            .aggregate(Sum('value'))['value__sum']

        return Response({ 'balance': total_sum })

    def get_filter(self):
        payed = self.request.query_params.get('payed', None)
        until = self.request.query_params.get('until', None)

        if payed is not None:
            return { 'payment_date__isnull': (payed == 0) }

        if until is not None:
            return { 'due_date__lte': datetime.strptime(until, '%Y-%m-%d') }

        return { 'due_date__lte': datetime.today() }