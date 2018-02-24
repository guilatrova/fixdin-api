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
        report = self._get_query()

        return list(report)

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
                    total=Sum('value')
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

class LastMonthsPayedReportFactory(LastMonthsReportFactory):
    '''
    Calculates sum of expenses, incomes and total over last 12 months + (13) actual month, but
    based on payment_date
    '''

    # def _get_query(self):
    #     start_date = self.get_start_date()

    #     return Transaction.objects.\
    #             filter(payment_date__gte=start_date, account__user_id=self.user_id).\
    #             annotate(date=TruncMonth('payment_date')).\
    #             values('date', 'kind').\
    #             annotate(total=Sum('value')).\
    #             order_by('date')