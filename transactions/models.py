from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator
from transactions.managers import TransactionsQuerySet

class BoundReasons:
    PERIODIC_TRANSACTION = "PERIODIC"
    TRANSFER_BETWEEN_ACCOUNTS = "ACCOUNT_TRANSFER"

class HasKind:
    EXPENSE_KIND = 0
    INCOME_KIND = 1

class Account(models.Model):
    user = models.ForeignKey(User)
    name = models.CharField(max_length=30)
    current_real_balance = models.DecimalField(max_digits=19, decimal_places=2)
    current_effective_balance = models.DecimalField(max_digits=19, decimal_places=2)

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

class Transaction(models.Model, HasKind):
    objects = TransactionsQuerySet.as_manager()

    TRANSACTION_KINDS = (
        (HasKind.EXPENSE_KIND, 'Expense'),
        (HasKind.INCOME_KIND, 'Income')
    )

    BOUND_REASON_CHOICES = (
        (BoundReasons.PERIODIC_TRANSACTION, "Periodic transaction"),
        (BoundReasons.TRANSFER_BETWEEN_ACCOUNTS, "Transfer between accounts")
    )

    def __init__(self, *args, **kwargs):
        '''
        Init method used to identify which values are loaded from database, 
        so we can identify if it suffered any changes after that.
        '''
        super(Transaction, self).__init__(*args, **kwargs)
        self.initial_value = self.value
        self.initial_due_date = self.due_date
        self.initial_payment_date = self.payment_date
        self.initial_account = self.account

    account = models.ForeignKey(Account)
    due_date = models.DateField()
    description = models.CharField(max_length=120)
    category = models.ForeignKey(Category)
    value = models.DecimalField(max_digits=19, decimal_places=2)
    kind = models.PositiveIntegerField(choices=TRANSACTION_KINDS)
    details = models.CharField(max_length=500, blank=True)   
    priority = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(5)])
    deadline = models.PositiveIntegerField(default=0)
    payment_date = models.DateField(null=True, blank=True) # TODO: Find out why both null and blank
    bound_transaction = models.ForeignKey("Transaction", null=True, on_delete=models.DO_NOTHING)
    bound_reason = models.CharField(max_length=20, choices=BOUND_REASON_CHOICES, blank=True)
    generic_tag = models.TextField(null=True, blank=True)
    """Generic text field to be used for third party and other stuff"""

    @property
    def real_value(self):
        """Gets the real value of transaction"""
        return self.value if self.payment_date else 0