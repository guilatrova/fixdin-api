from datetime import datetime
from django.db.models import Sum
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view
from common import dates_utils
from transactions.models import Category, Transaction, Account
from balances import queries
from balances.builders import CalculatorBuilder
from balances.strategies.query import based, outputs

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

    calculator = CalculatorBuilder()\
        .owned_by(request.user.id)\
        .consider(based.EFFECTIVE)\
        .between_dates(from_date, until_date)\
        .as_detailed()\
        .build()
        
    result = calculator.calculate()

    return Response(result)

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

consider_mapping = {
    'effective': based.EFFECTIVE,
    'real': based.REAL,
    'both': based.BOTH
}

@api_view()
def get_plain_balance(request, format='json'):
    builder = CalculatorBuilder()
    consider = consider_mapping.get(request.query_params.get('based', 'effective'))
    output = request.query_params.get('output', outputs.TOTAL)
    filters = {}
    pending = request.query_params.get('pending', False)
    if pending:
        filters['payment_date__isnull'] = True

    builder.owned_by(request.user.id).consider(consider)
    calculator = _apply_date(builder, request.query_params)\
        .as_plain(output=output)\
        .build()

    result = calculator.calculate(**filters)
    return Response({ 'balance': result })

@api_view()
def get_detailed_balance(request, format='json'):
    builder = CalculatorBuilder()
    consider = consider_mapping.get(request.query_params.get('based', 'effective'))

    builder.owned_by(request.user.id).consider(consider)
    calculator = _apply_date(builder, request.query_params)\
        .as_detailed()\
        .build()

    result = calculator.calculate()
    return Response(result)

def _apply_date(builder, query_params):
    specific_date = query_params.get('date', False)
    start = query_params.get('from', False)
    end = query_params.get('until', False)

    if specific_date:
        return builder.on_date(dates_utils.from_str(specific_date))

    if start and end:
        start = dates_utils.from_str(start)
        end = dates_utils.from_str(end)
        return builder.between_dates(start, end)

    if end:
        return builder.until(dates_utils.from_str(end))

    return builder.until(datetime.today())