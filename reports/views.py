from django.db.models import Sum
from django.db.models.functions import TruncMonth
from rest_framework.views import APIView
from rest_framework.response import Response
from datetime import datetime
from dateutil.relativedelta import relativedelta
from transactions.models import Transaction
from reports.serializers import Last13MonthsSerializer, PendingSerializer
from reports.factories.Last13MonthsReport import Last13MonthsReportFactory, Last13MonthsPayedReportFactory
from reports.factories.PendingReport import PendingExpensesReportFactory, PendingIncomesReportFactory

class Last13MonthsAPIView(APIView):

    def get(self, request, format='json'):
        payed_filter = request.query_params.get('payed', 0)

        if payed_filter == '1':
            report = Last13MonthsPayedReportFactory(request.user.id).generate_report()
        else:
            report = Last13MonthsReportFactory(request.user.id).generate_report()

        serialized = Last13MonthsSerializer(report, many=True).data
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