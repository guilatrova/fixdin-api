from datetime import datetime
from django.db.models import Sum
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view
from transactions.models import Category, Transaction, Account
from balances import queries

@api_view()
def get_balance(request, format='json'):
    additional_filters = _get_filter(request)
    total_sum = Transaction.objects\
        .filter(account__user_id=request.user.id, **additional_filters)\
        .aggregate(Sum('value'))['value__sum']

    return Response({ 'balance': total_sum })

@api_view()
def get_total_pending_incomes(request, format='json'):
    total = queries.get_total_pending_incomes(request.user.id)
    return Response({ 'balance': total })

def _get_filter(request):
    payed = request.query_params.get('payed', None)
    until = request.query_params.get('until', None)

    if payed is not None:
        return { 'payment_date__isnull': (payed == 0) }

    if until is not None:
        return { 'due_date__lte': datetime.strptime(until, '%Y-%m-%d') }

    return { 'due_date__lte': datetime.today() }