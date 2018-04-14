from .BaseStrategy import BaseStrategy
from .outputs import EXPENSES, INCOMES, TOTAL
from transactions.models import HasKind
from django.db.models import Sum, Case, When, F
from django.db.models.functions import Coalesce

sum_when = lambda **kwargs : Coalesce(Sum(Case(When(then=F('value'), **kwargs), default=0)), 0) #TODO: move it somewhere else

class PlainFormatStrategy(BaseStrategy):
    """
    Aggregates balance to generate a plain value
    """

    def __init__(self, output=TOTAL):
        """
        Initializes strategy class

        :param output: String determines which transactions should be aggregated (expenses, incomes or total)
        """
        self.output = output

    def apply(self, query):
        if self.output == EXPENSES:
            query = query.expenses()
        elif self.output == INCOMES:
            query = query.incomes()
            
        return query.aggregate(Sum('value'))['value__sum']

class DetailedFormatStrategy(BaseStrategy):
    """
    Annotates balance split in expenses, incomes and total values
    """

    def apply(self, query):
        return query.aggregate(
            incomes=sum_when(kind=HasKind.INCOME_KIND),
            expenses=sum_when(kind=HasKind.EXPENSE_KIND),
            total=Sum('value')
        )