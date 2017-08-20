from django.db.models import Sum
from django.db.models.functions import TruncMonth
from datetime import datetime
import calendar
from dateutil.relativedelta import relativedelta
from transactions.models import Transaction

class NextExpensesReportFactory:

    def __init__(self, user_id):
        self.user_id = user_id

    def generate_report(self):
        data = self._get_query()
        report = self.aggregate_by_due_date(list(data))

        return report

    def _get_query(self):
        return Transaction.objects.filter(
            payment_date__isnull=True,
            kind=Transaction.EXPENSE_KIND,
            account__user_id=self.user_id)\
            .order_by('-priority', 'due_date', 'deadline')

    def aggregate_by_due_date(self, data):
        today = datetime.today().date()

        dic = {}
        dic['overdue'] = [x for x in data if x.due_date < today]
        dic['next'] = [x for x in data if x.due_date >= today]

        return dic