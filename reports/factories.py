from django.db.models import Sum
from django.db.models.functions import TruncMonth
from datetime import datetime
from dateutil.relativedelta import relativedelta
from transactions.models import Transaction

class Last13MonthsReportFactory:

    def generate_report(self):
        data = self.get_query()
        
        report = list(data)
        if (len(report)) < 13:
            report = self.insert_missing_periods(report)

        return report

    def get_query(self):
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

    def insert_missing_periods(self, data):
        expected_date = self.get_start_date()
        new_data = []
        delay = 0

        for i in range(13):

            if (data[i - delay]['date'] != expected_date.date()):
                new_data.append({ "date": expected_date, "total": 0 })
                delay = delay + 1
            else:
                new_data.append(data[i - delay])
            
            expected_date = expected_date + relativedelta(months=1)

        return new_data
