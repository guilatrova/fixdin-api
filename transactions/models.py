from django.db import models
from django.contrib.auth.models import User

class Category(models.Model):
    class Meta:
        unique_together = ('user', 'name')

    EXPENSE_KIND = 0
    INCOME_KIND = 1
        
    CATEGORY_KINDS = (
        (EXPENSE_KIND, 'Expense'),
        (INCOME_KIND, 'Income')
    )

    name = models.CharField(max_length=30)
    user = models.ForeignKey(User)
    kind = models.PositiveIntegerField(choices=CATEGORY_KINDS)

class Account(models.Model):
    user = models.ForeignKey(User)
    name = models.CharField(max_length=30)
    current_balance = models.DecimalField(max_digits=19, decimal_places=2)

class Transaction(models.Model):
    EXPENSE_KIND = 0
    INCOME_KIND = 1

    def __init__(self, *args, **kwargs):
        '''
        Init method used to identify which value is loaded from database, 
        so we can identify if it suffered any changes after that.
        '''
        super(Transaction, self).__init__(*args, **kwargs)
        self.initial_value = self.value

    account = models.ForeignKey(Account)
    due_date = models.DateField()
    description = models.CharField(max_length=120)
    category = models.ForeignKey(Category)
    value = models.DecimalField(max_digits=19, decimal_places=2)
    payed = models.BooleanField()
    details = models.CharField(max_length=500, blank=True)   
    periodic_transaction = models.ForeignKey("Transaction", null=True)
    
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
