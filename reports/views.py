from django.db.models import Sum
from django.db.models.functions import TruncMonth
from rest_framework.views import APIView
from rest_framework.response import Response
from datetime import datetime
from dateutil.relativedelta import relativedelta
from transactions.models import Transaction
from reports.serializers import Last13MonthsSerializer, PendingSerializer
from reports.factories.Last13MonthsReport import Last13MonthsReportFactory
from reports.factories.PendingReport import PendingExpensesReportFactory

class Last13MonthsAPIView(APIView):

    def get(self, request, format='json'):        
        report = Last13MonthsReportFactory(request.user.id).generate_report()
        serialized = Last13MonthsSerializer(report, many=True).data
        return Response(serialized)

class PendingAPIView(APIView):
    
    def get(self, request, format='json'):
        report = PendingExpensesReportFactory(request.user.id).generate_report()
        serialized = PendingSerializer(report).data
        return Response(serialized)