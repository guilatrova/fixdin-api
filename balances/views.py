from datetime import datetime
from django.db.models import Sum
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view
from common import dates_utils
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
def get_accumulated_balance(request, format='json'):
    from_date = request.query_params.get('from', None)
    until_date = request.query_params.get('until', None)
    if from_date is None or until_date is None: #TODO: test this
        from_date, until_date = dates_utils.get_year_range()

    total = queries.get_accumulated_detailed(request.user.id, from_date, until_date)
    return Response(total)

@api_view()
def get_total_pending_incomes(request, format='json'):
    """Returns actual balance summing all pending incomes"""
    total = queries.get_total_pending_incomes(request.user.id)
    return Response({ 'balance': total })

@api_view()
def get_total_pending_expenses(request, format='json'):
    """Returns actual balance summing all pending expenses"""
    total = queries.get_total_pending_expenses(request.user.id)
    return Response({ 'balance': total })

@api_view()
def get_effective_incomes_expenses_by_account(request, format='json'):
    accounts = queries.get_effective_incomes_expenses_by_account(request.user.id)    
    return Response(accounts)

def _get_filter(request):
    payed = request.query_params.get('payed', None)
    until = request.query_params.get('until', None)

    if payed is not None:
        return { 'payment_date__isnull': (payed == 0) }

    if until is not None:
        return { 'due_date__lte': datetime.strptime(until, '%Y-%m-%d') }

    return { 'due_date__lte': datetime.today() }

#REFACTOR

@api_view()
def get_plain_balance(request, format='json'):
    from_date = request.query_params