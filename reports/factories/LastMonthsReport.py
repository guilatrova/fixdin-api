from itertools import takewhile
from django.db.models import Q, Sum, Case, When, F
from django.db.models.functions import Coalesce, TruncMonth, TruncYear
from datetime import datetime
import calendar
from dateutil.relativedelta import relativedelta
from transactions.models import Transaction, HasKind

class LastMonthsReportFactory:
    '''
    Calculates sum of expenses, incomes and total over last months.
    '''

    def __init__(self, user_id, months):
        self.user_id = user_id
        self.months = months

    def generate_report(self):
        report = list(self._get_query())
        self._add_missing_periods(report)

        return report
        
    def _add_missing_periods(self, data):
        cur_date = self.get_start_date()
        end_date = self.get_end_date()
        expected_dates = []

        while cur_date < end_date:
            expected_dates.append(cur_date.date())
            cur_date += relativedelta(months=1)

        if len(expected_dates) > len(data):
            for i in range(len(expected_dates)):
                item = data[i]
                if item['date'] != expected_dates[i]:
                    data.insert(i, { "date": expected_dates[i], "effective_expenses": 0, "effective_incomes": 0, "real_expenses": 0, "real_incomes": 0, "effective_total": 0})
        
        assert len(expected_dates) == len(data), \
            "Amount of rows should match amount of expected periods. Periods: {} Rows: {}".format(len(expected_dates), len(data))

    def _get_query(self):
        start_date = self.get_start_date()
        sum_when = lambda **kwargs : Coalesce(Sum(Case(When(then=F('value'), **kwargs), default=0)), 0)
        sum_kind = lambda kind : sum_when(kind=kind)
        sum_kind_payed = lambda kind : sum_when(kind=kind, payment_date__month=F('date'))

        #TruncMonth cares about year too
        return Transaction.objects.\
                filter(account__user_id=self.user_id, due_date__gte=start_date).\
                annotate(date=TruncMonth('due_date')).\
                values('date').\
                annotate(
                    effective_expenses=sum_kind(HasKind.EXPENSE_KIND),
                    effective_incomes=sum_kind(HasKind.INCOME_KIND),
                    real_expenses=sum_kind_payed(HasKind.EXPENSE_KIND),
                    real_incomes=sum_kind_payed(HasKind.INCOME_KIND),
                    effective_total=Sum('value')
                ).\
                order_by('date')

    def get_start_date(self):
        today = datetime.today()
        relative = today + relativedelta(months=-self.months)
        return datetime(relative.year, relative.month, 1)

    def get_end_date(self):
        today = datetime.today()
        last_day = calendar.monthrange(today.year, today.month)[1]
        return datetime(today.year, today.month, last_day)