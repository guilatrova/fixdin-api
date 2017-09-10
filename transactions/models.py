from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator

class HasKind:
    EXPENSE_KIND = 0
    INCOME_KIND = 1

class Category(models.Model, HasKind):
    class Meta:
        unique_together = ('user', 'name', 'kind')    
        
    CATEGORY_KINDS = (
        (HasKind.EXPENSE_KIND, 'Expense'),
        (HasKind.INCOME_KIND, 'Income')
    )

    name = models.CharField(max_length=70)
    user = models.ForeignKey(User)
    kind = models.PositiveIntegerField(choices=CATEGORY_KINDS)

class Account(models.Model):
    user = models.ForeignKey(User)
    name = models.CharField(max_length=30)
    current_balance = models.DecimalField(max_digits=19, decimal_places=2)

class Transaction(models.Model, HasKind):

    TRANSACTION_KINDS = (
        (HasKind.EXPENSE_KIND, 'Expense'),
        (HasKind.INCOME_KIND, 'Income')
    )

    def __init__(self, *args, **kwargs):
        '''
        Init method used to identify which value (R$) is loaded from database, 
        so we can identify if it suffered any changes after that.
        '''
        super(Transaction, self).__init__(*args, **kwargs)
        self.initial_value = self.value

    account = models.ForeignKey(Account)
    due_date = models.DateField()
    description = models.CharField(max_length=120)
    category = models.ForeignKey(Category)
    value = models.DecimalField(max_digits=19, decimal_places=2)
    kind = models.PositiveIntegerField(choices=TRANSACTION_KINDS)
    details = models.CharField(max_length=500, blank=True)   
    periodic_transaction = models.ForeignKey("Transaction", null=True, on_delete=models.DO_NOTHING)
    priority = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(5)])
    deadline = models.PositiveIntegerField(default=0)
    payment_date = models.DateField(null=True, blank=True)