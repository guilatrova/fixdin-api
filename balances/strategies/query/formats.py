from .BaseStrategy import BaseStrategy
from .outputs import EXPENSES, INCOMES, TOTAL
from transactions.models import HasKind, Account
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

class DetailedAccountFormatStrategy(BaseStrategy):
    """
    Annotates balance split in accounts, and then into expenses, incomes and total values
    """

    def __init__(self, user_id):
        """
        Initializes strategy class

        :param user_id: Id that represents user
        """
        self.user_id = user_id

    def apply(self, query):
        accounts = query.values('account').annotate(
            incomes=sum_when(kind=HasKind.INCOME_KIND),
            expenses=sum_when(kind=HasKind.EXPENSE_KIND),
            total=Sum('value')
        )\
        .order_by('account')

        missing_accounts = Account.objects\
            .filter(user_id=self.user_id)\
            .exclude(id__in=accounts.values_list('account_id', flat=True))\
            .values_list('id', flat=True)

        result = list(accounts)

        for missing in missing_accounts:
            result.append({
                'account': missing,
                'incomes': 0,
                'expenses': 0,
                'total': 0
            })

        return result