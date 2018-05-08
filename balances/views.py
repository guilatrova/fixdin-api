from datetime import datetime
from django.db.models import Sum
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view
from common import dates_utils
from transactions.models import Category, Transaction, Account
from balances.factories import CalculatorBuilder, PeriodQueryBuilder
from balances.strategies.query import based, outputs
from balances.serializers import PeriodSerializer

consider_mapping = {
    'effective': based.EFFECTIVE,
    'real': based.REAL,
    'both': based.BOTH
}

class BaseBalanceAPIView(APIView):

    def get(self, request, format='json'):
        filters = self.create_filters()
        consider = consider_mapping.get(request.query_params.get('based', 'effective'))        

        builder = self.create_builder(consider)
        
        calculator = self.create_calculator(builder)
        result = calculator.calculate(**filters)

        return self.create_response(result)

    def create_response(self, result):
        return Response(result)

    def create_builder(self, consider):
        builder = CalculatorBuilder()\
            .owned_by(self.request.user.id)\
            .consider(consider)

        return self.apply_date(builder)

    def create_filters(self):
        filters = {}
        pending = self.request.query_params.get('pending', False)
        if pending:
            filters['payment_date__isnull'] = True

        return filters

    def apply_date(self, builder):
        query_params = self.request.query_params
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

class PlainBalanceAPIView(BaseBalanceAPIView):
    def create_response(self, result):
        return Response({ 'balance': result })

    def create_calculator(self, builder):
        output = self.request.query_params.get('output', outputs.TOTAL)
        return builder.as_plain(output=output).build()

class DetailedBalanceAPIView(BaseBalanceAPIView):
    def create_calculator(self, builder):
        return builder.as_detailed().build()

class DetailedAccountsBalanceAPIView(BaseBalanceAPIView):
    def create_calculator(self, builder):
        return builder.as_detailed_accounts().build()

@api_view()
def get_periods(request):
    cur_date = datetime.today()
    get_date = lambda: '{year}-{month}-01'.format(year=cur_date.year, month=cur_date.month)

    start = dates_utils.from_str(request.query_params.get('from', get_date()))
    end = dates_utils.from_str(request.query_params.get('until', get_date()))

    factory = PeriodQueryBuilder(request.user.id, start, end)
    query = factory.build()
    serialized = PeriodSerializer(query, many=True).data
    return Response(serialized)