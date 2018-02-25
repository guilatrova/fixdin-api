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

    def __init__(self, user_id, months):
        self.user_id = user_id
        self.months = months

    def generate_report(self):
        data = list(self._get_query())
        report = self._merge_union(data)
        self._add_missing_periods(report)

        return report

    def _merge_union(self, data):
        merged = []
        for row in data:
            def filter_date(x): return x['date'] == row['date']

            if not any(row['date'] == x['date'] for x in merged):
                same_periods = list(filter(filter_date, data))
                if len(same_periods) > 1:
                    result = self._sum_dict(same_periods)
                else:
                    result = same_periods[0]
                merged.append(result)

        return merged

    def _sum_dict(self, lst):
        ret = defaultdict(int)
        for d in lst:
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
                item = data[i]
                if item['date'] != expected_dates[i]:
                    data.insert(i, { "date": expected_dates[i], "effective_expenses": 0, "effective_incomes": 0, "real_expenses": 0, "real_incomes": 0, "effective_total": 0})
        
        assert len(expected_dates) == len(data), \
            "Amount of rows should match amount of expected periods. Periods: {} Rows: {}".format(len(expected_dates), len(data))

    def _get_query(self):
        start_date = self.get_start_date()

        #TruncMonth cares about year too
        transactions = Transaction.objects.filter(
            Q(account__user_id=self.user_id),
            Q(due_date__gte=start_date) | Q(payment_date__gte=start_date)
        )
        due = transactions
        payed = transactions.filter(payment_date__isnull=False)\
            .exclude(
                payment_date__month=ExtractMonth('due_date'),
                payment_date__year=ExtractYear('due_date')
            )

        due_result = self._sum_queryset('due_date', due)
        payed_result = self._sum_queryset('payment_date', payed)

        return due_result.union(payed_result).order_by('date')        

    def _sum_queryset(self, field, queryset):
        sum_when = lambda **kwargs : Coalesce(Sum(Case(When(then=F('value'), **kwargs), default=0)), 0)
        sum_effective = lambda **kwargs : sum_when(**kwargs, due_date__month=ExtractMonth('date'), due_date__year=ExtractYear('date'))
        sum_real = lambda **kwargs : sum_when(**kwargs, payment_date__month=ExtractMonth('date'), payment_date__year=ExtractYear('date'))
        sum_kind = lambda kind : sum_effective(kind=kind)
        sum_kind_payed = lambda kind : sum_real(kind=kind)

        return queryset.annotate(date=TruncMonth(field))\
            .values('date')\
            .annotate(
                effective_expenses=sum_kind(HasKind.EXPENSE_KIND),
                effective_incomes=sum_kind(HasKind.INCOME_KIND),
                real_expenses=sum_kind_payed(HasKind.EXPENSE_KIND),
                real_incomes=sum_kind_payed(HasKind.INCOME_KIND),
                effective_total=sum_effective(),
                real_total=sum_real()
            )            

    def get_start_date(self):
        today = datetime.today()
        relative = today + relativedelta(months=-self.months)
        return datetime(relative.year, relative.month, 1)

    def get_end_date(self):
        today = datetime.today()
        last_day = calendar.monthrange(today.year, today.month)[1]
        return datetime(today.year, today.month, last_day)