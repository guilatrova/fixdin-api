from django.db.models import Sum
from django.db.models.functions import TruncMonth
from datetime import datetime
import calendar
from dateutil.relativedelta import relativedelta
from transactions.models import Transaction

class Last13MonthsReportFactory:

    def generate_report(self):
        data = self._get_query()
        report = self.aggregate_transactions(list(data))

        return report

    def aggregate_transactions(self, data):
        cur_date = self.get_start_date()
        end_date = self.get_end_date()
        aggregated = []

        while cur_date < end_date:
            transactions_in_date = [x for x in data if x['date'] == cur_date.date()]
            expenses = sum([x['total'] for x in transactions_in_date if x['kind'] == Transaction.EXPENSE_KIND])
            incomes = sum([x['total'] for x in transactions_in_date if x['kind'] == Transaction.INCOME_KIND])
            total = expenses + incomes

            aggregated.append({ "date": cur_date, "expenses": expenses, "incomes": incomes, "total": total })
            cur_date = cur_date + relativedelta(months=1)

        return aggregated            

    def _get_query(self):
        start_date = self.get_start_date()

        return Transaction.objects.\
                filter(due_date__gte=start_date).\
                annotate(date=TruncMonth('due_date')).\
                values('date', 'kind').\
                annotate(total=Sum('value')).\
                order_by('date')

    def get_start_date(self):
        today = datetime.today()
        relative = today + relativedelta(months=-12)
        return datetime(relative.year, relative.month, 1)

    def get_end_date(self):
        today = datetime.today()
        last_day = calendar.monthrange(today.year, today.month)[1]
        return datetime(today.year, today.month, last_day)