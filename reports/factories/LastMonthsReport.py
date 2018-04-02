from datetime import datetime, date
from collections import defaultdict
from functools import reduce
from django.db.models import Q, Sum, Case, When, F, Value, CharField
from django.db.models.functions import Coalesce, TruncMonth, ExtractMonth, ExtractYear
import calendar
from dateutil.relativedelta import relativedelta
from transactions.models import Transaction, HasKind

class LastMonthsReportFactory:
    '''
    Calculates sum of expenses, incomes and total over last months.
    '''

    def __init__(self, user_id, months, start=None): #TODO: Refactor this start thing
        self.user_id = user_id
        self.months = months
        self.start = start

    def generate_report(self):
        data = list(self._get_query())
        report = self._merge_union(data)
        self._add_missing_periods(report)

        return report

    def get_start_date(self):
        if self.start:            
            return datetime(self.start.year, self.start.month, 1)
        today = datetime.today()
        relative = today + relativedelta(months=-self.months)
        return datetime(relative.year, relative.month, 1)

    def get_end_date(self):
        if self.start:
            end = self.start + relativedelta(months=self.months)
            last_day = calendar.monthrange(end.year, end.month)[1]
            return datetime(end.year, end.month, last_day)
        today = datetime.today()
        last_day = calendar.monthrange(today.year, today.month)[1]
        return datetime(today.year, today.month, last_day)

    def _get_query(self):
        start_date = self.get_start_date()
        end_date = self.get_end_date()
        
        user_transactions = Transaction.objects.owned_by(self.user_id)
        due = user_transactions.filter(due_date__range=[start_date, end_date])
        payed_out_due = user_transactions.filter(payment_date__range=[start_date, end_date])\
            .exclude(
                payment_date__month=ExtractMonth('due_date'),
                payment_date__year=ExtractYear('due_date')
            )

        due_result = self._sum_queryset('due_date', due)
        payed_result = self._sum_queryset('payment_date', payed_out_due)

        return due_result.union(payed_result).order_by('date')

    def _sum_queryset(self, field, queryset):
        sum_when = lambda **kwargs : Coalesce(Sum(Case(When(then=F('value'), **kwargs), default=0)), 0)
        sum_effective = lambda **kwargs : sum_when(**kwargs, due_date__month=ExtractMonth('date'), due_date__year=ExtractYear('date'))
        sum_real = lambda **kwargs : sum_when(**kwargs, payment_date__isnull=False, payment_date__month=ExtractMonth('date'), payment_date__year=ExtractYear('date'))
        sum_effective_kind = lambda kind : sum_effective(kind=kind)
        sum_real_kind = lambda kind : sum_real(kind=kind)

        #TruncMonth cares about year too
        return queryset.annotate(date=TruncMonth(field))\
            .values('date')\
            .annotate(
                effective_expenses=sum_effective_kind(HasKind.EXPENSE_KIND),
                effective_incomes=sum_effective_kind(HasKind.INCOME_KIND),
                real_expenses=sum_real_kind(HasKind.EXPENSE_KIND),
                real_incomes=sum_real_kind(HasKind.INCOME_KIND),
                effective_total=sum_effective(),
                real_total=sum_real()
            )

    def _merge_union(self, data):
        merged = []
        not_merged = lambda date : not any(date == x['date'] for x in merged)
        filter_date = lambda date : lambda x : x['date'] == date

        for row in data:
            if not_merged(row['date']):
                same_periods = filter(filter_date(row['date']), data)
                result = self._sum_dicts(same_periods)
                merged.append(result)

        return merged

    @staticmethod
    def _sum_dicts(dicts):
        ret = defaultdict(int)
        for d in dicts:
            for k, v in d.items():
                if (isinstance(v, date)):
                    ret[k] = v
                else:
                    ret[k] += v
        return dict(ret)

    def _add_missing_periods(self, data):
        cur_date = self.get_start_date()
        end_date = self.get_end_date()
        expected_dates = []

        while cur_date < end_date:
            expected_dates.append(cur_date.date())
            cur_date += relativedelta(months=1)

        if len(expected_dates) > len(data):
            for i in range(len(expected_dates)):
                item = data[i] if len(data) > i else { 'date': None }
                if item['date'] != expected_dates[i]:
                    data.insert(i, { "date": expected_dates[i], "effective_expenses": 0, "effective_incomes": 0, "real_expenses": 0, "real_incomes": 0, "effective_total": 0, "real_total": 0})
        
        assert len(expected_dates) == len(data), \
            "Amount of rows should match amount of expected periods. Periods: {} Rows: {}".format(len(expected_dates), len(data))