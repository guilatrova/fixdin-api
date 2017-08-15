from django.db import models
from transactions.models import Transaction, Account

class PeriodBalance(models.Model):
    account = models.ForeignKey(Account)
    start_date = models.DateField()
    end_date = models.DateField()
    last_updated = models.DateField(auto_now=True)
    closed_value = models.DecimalField(max_digits=19, decimal_places=2)

    def get_transactions(self):
        return Transaction.objects.filter(
            due_date__gte=self.start_date,
            due_date__lte=self.end_date)
