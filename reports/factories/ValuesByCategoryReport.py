from django.db.models import Sum
from django.db.models.functions import TruncMonth
from datetime import datetime
import calendar
from dateutil.relativedelta import relativedelta
from transactions.models import Transaction

class ValuesByCategoryReportFactory:
    '''
    Calculates sum of transactions aggregated by category
    '''

    def __init__(self, user_id, **filters):
        self.user_id = user_id
        self.filters = filters

    def generate_report(self):
        data = self._get_query()
        report = self._ignore_signals(data)        
        
        return report

    def _ignore_signals(self, query):
        fixed = []
        for aggregation in query:
            if (aggregation['total'] < 0):
                aggregation['total'] *= -1
            fixed.append(aggregation)

        return fixed

    def _get_query(self):
        return Transaction.objects.filter(kind=self.filters['kind'], account__user_id=self.user_id)\
                .values('category_id')\
                .annotate(total=Sum('value'))\
                .order_by('category_id')