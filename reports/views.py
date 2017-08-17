from django.db.models import Sum
from django.db.models.functions import TruncMonth
from rest_framework.views import APIView
from rest_framework.response import Response
from datetime import datetime
from dateutil.relativedelta import relativedelta
from transactions.models import Transaction
from reports.serializers import Last13DaysSerializer

class Last30MonthsAPIView(APIView):

    def get(self, request, format='json'):        
        start_date = self.get_start_date()
        last_13_months = Transaction.objects.filter(due_date__gte=start_date)
        result = last_13_months.\
                    annotate(date=TruncMonth('due_date')).\
                    values('date').\
                    annotate(total=Sum('value')).\
                    order_by()

        data = list(result)
        serialized = Last13DaysSerializer(data, many=True).data
        return Response(serialized)

    def get_start_date(self):
        today = datetime.today()
        relative = today + relativedelta(months=-12)
        return datetime(relative.year, relative.month, 1)