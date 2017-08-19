from django.db.models import Sum
from django.db.models.functions import TruncMonth
from rest_framework.views import APIView
from rest_framework.response import Response
from datetime import datetime
from dateutil.relativedelta import relativedelta
from transactions.models import Transaction
from reports.serializers import Last13MonthsSerializer

class Last13MonthsAPIView(APIView):

    def get(self, request, format='json'):        
        start_date = self.get_start_date()
        last_13_months = Transaction.objects.filter(due_date__gte=start_date)
        result = last_13_months.\
                    annotate(date=TruncMonth('due_date')).\
                    values('date').\
                    annotate(total=Sum('value')).\
                    order_by()

        data = list(result)            
        if (len(data)) < 13:
            data = self.insert_missing_periods(data)

        serialized = Last13MonthsSerializer(data, many=True).data
        return Response(serialized)

    def insert_missing_periods(self, data):
        expected_date = self.get_start_date()
        new_data = []
        delay = 0

        for i in range(13):

            if (data[i - delay]['date'] != expected_date.date()):
                new_data.append({ "date": expected_date, "total": 0 })
                delay = delay + 1
            else:
                new_data.append(data[i - delay])
            
            expected_date = expected_date + relativedelta(months=1)

        return new_data

    def get_start_date(self):
        today = datetime.today()
        relative = today + relativedelta(months=-12)
        return datetime(relative.year, relative.month, 1)