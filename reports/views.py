from django.db.models import Sum
from django.db.models.functions import TruncMonth
from rest_framework.views import APIView
from rest_framework.response import Response
from datetime import datetime
from dateutil.relativedelta import relativedelta
from transactions.models import Transaction
from reports.serializers import LastMonthsSerializer, PendingSerializer, ValuesByCategorySerializer
from reports.factories.LastMonthsReport import LastMonthsReportFactory, LastMonthsPayedReportFactory
from reports.factories.PendingReport import PendingExpensesReportFactory, PendingIncomesReportFactory
from reports.factories.ValuesByCategoryReport import ValuesByCategoryReportFactory

class LastMonthsAPIView(APIView):

    def get(self, request, format='json'):
        payed_filter = request.query_params.get('payed', 0)

        if payed_filter == '1':
            report = LastMonthsPayedReportFactory(request.user.id, 13).generate_report()
        else:
            report = LastMonthsReportFactory(request.user.id, 13).generate_report()

        serialized = LastMonthsSerializer(report, many=True).data
        return Response(serialized)

class PendingAPIView(APIView):
    
    def get(self, request, kind, format='json'):
        if kind == Transaction.EXPENSE_KIND:
            report_factory = PendingExpensesReportFactory(request.user.id)
        else:
            report_factory = PendingIncomesReportFactory(request.user.id)
        
        report = report_factory.generate_report()
        serialized = PendingSerializer(report).data
        return Response(serialized)

class ValuesByCategoryAPIView(APIView):

    def get(self, request, kind, format='json'):
        kind = Transaction.EXPENSE_KIND if kind == 'expenses' else Transaction.INCOME_KIND
        report_factory = ValuesByCategoryReportFactory(request.user.id, kind=kind)

        report = report_factory.generate_report()
        serialized = ValuesByCategorySerializer(report, many=True).data
        return Response(serialized)