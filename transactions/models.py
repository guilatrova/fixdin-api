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

class Transaction(models.Model):
    due_date = models.DateField()
    description = models.CharField(max_length=120)
    category = models.ForeignKey(Category)
    value = models.DecimalField(max_digits=19, decimal_places=2)
    payed = models.BooleanField()
    details = models.CharField(max_length=500, blank=True)
    user = models.ForeignKey(User)