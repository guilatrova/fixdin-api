from django.db import models
from django.db.models import Q

from transactions.models import Account, Transaction


class PeriodBalance(models.Model):
    account = models.ForeignKey(Account)
    start_date = models.DateField()
    end_date = models.DateField()
    last_updated = models.DateField(auto_now=True)
    closed_effective_value = models.DecimalField(max_digits=19, decimal_places=2)
    closed_real_value = models.DecimalField(max_digits=19, decimal_places=2)

    def get_transactions(self):
        return Transaction.objects.in_date_range(self.start_date, self.end_date)
