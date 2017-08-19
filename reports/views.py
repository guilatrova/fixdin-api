from django.db.models import Sum
from django.db.models.functions import TruncMonth
from rest_framework.views import APIView
from rest_framework.response import Response
from datetime import datetime
from dateutil.relativedelta import relativedelta
from transactions.models import Transaction
from reports.serializers import Last13MonthsSerializer
from reports.factories import Last13MonthsReportFactory

class Last13MonthsAPIView(APIView):

    def get(self, request, format='json'):        
        report = Last13MonthsReportFactory().generate_report()
        serialized = Last13MonthsSerializer(report, many=True).data
        return Response(serialized)