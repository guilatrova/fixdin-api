from datetime import datetime
from transactions.models import Transaction

class PendingReportFactory:

    def __init__(self, user_id):
        self.user_id = user_id

    def generate_report(self):
        data = self._get_query()
        report = self.aggregate_by_due_date(list(data))

        return report

    def _get_query(self):
        filters = self._get_filters()

        return Transaction.objects\
            .filter(**filters)\
            .order_by('-priority', 'due_date', 'deadline')

    def aggregate_by_due_date(self, data):
        today = datetime.today().date()

        dic = {}
        dic['overdue'] = [x for x in data if x.due_date < today]
        dic['next'] = [x for x in data if x.due_date >= today]

        return dic

class PendingExpensesReportFactory(PendingReportFactory):

    def _get_filters(self):
        return {
            "payment_date__isnull": True,
            "kind": Transaction.EXPENSE_KIND,
            "account__user_id": self.user_id
        }

class PendingIncomesReportFactory(PendingReportFactory):

    def _get_filters(self):
        return {
            "payment_date__isnull": True,
            "kind": Transaction.INCOME_KIND,
            "account__user_id": self.user_id
        }