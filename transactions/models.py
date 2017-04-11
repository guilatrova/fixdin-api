from django.db import models
from django.contrib.auth.models import User

class Category(models.Model):
    EXPENSE_KIND = 0
    INCOME_KIND = 1
        
    CATEGORY_KINDS = (
        (EXPENSE_KIND, 'Expense'),
        (INCOME_KIND, 'Income')
    )

    name = models.CharField(max_length=30)
    user = models.ForeignKey(User)
    kind = models.PositiveIntegerField(choices=CATEGORY_KINDS)