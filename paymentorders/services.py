from django.db.models.functions import TruncMonth
from datetime import date
from dateutil.relativedelta import relativedelta
from common import dates_utils
from itertools import groupby
from transactions.models import Transaction, HasKind

class NextExpensesService:
    def __init__(self, user_id, from_date, until_date):
        self.user_id = user_id
        self.from_date = date(from_date.year, from_date.month, 1)
        self.until_date = dates_utils.get_last_day_of(until_date)

    def generate_data(self):
        queryset = self._generate_queryset()
        return self._group_queryset_over_dates(queryset)

    def _generate_queryset(self):
        return Transaction.objects.\
            owned_by(self.user_id).\
            expires_between(self.from_date, self.until_date).\
            filter(
                kind=HasKind.EXPENSE_KIND
            ).annotate(
                date=TruncMonth('due_date')
            ).order_by('description')

    def _group_queryset_over_dates(self, queryset):
        groupped = []
        result = []
        dates = self._get_dates()
        data = list(queryset)

        for key, group in groupby(data, lambda x: x.description):
            groupped.append(list(group))
        
        for group in groupped:
            group_date = {}
            for date in dates:
                group_date[date.strftime('%Y-%m-%d')] = [ transaction for transaction in group if transaction.date == date ]
            result.append(group_date)

        return result

    def _get_dates(self):
        cur_date = self.from_date
        result = []

        while cur_date <= self.until_date:
            result.append(cur_date)
            cur_date += relativedelta(months=1)

        return result
