from django.db.models import Sum
from django.db.models.functions import TruncMonth
from rest_framework.views import APIView
from rest_framework.response import Response
from datetime import datetime
from dateutil.relativedelta import relativedelta
from transactions.models import Transaction
from reports.serializers import Last13MonthsSerializer
from transactions.serializers import TransactionSerializer
from reports.factories.Last13MonthsReport import Last13MonthsReportFactory
from reports.factories.NextExpensesReport import NextExpensesReportFactory

class Last13MonthsAPIView(APIView):

    def get(self, request, format='json'):        
        report = Last13MonthsReportFactory(request.user.id).generate_report()
        serialized = Last13MonthsSerializer(report, many=True).data
        return Response(serialized)

class NextExpenses(APIView):
    
    def get(self, request, format='json'):
        report = NextExpensesReportFactory(request.user.id).generate_report()
        serialized = TransactionSerializer(report, many=True).data
        return Response(serialized)