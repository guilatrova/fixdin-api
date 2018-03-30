from datetime import date
from django.db.models import Sum, Case, When, F
from django.db.models.functions import Coalesce
from common.dates_utils import get_start_end_month
from transactions.models import Transaction, HasKind

def get_total_pending_incomes(user_id):
    today = date.today()
    return Transaction.objects\
        .owned_by(user_id)\
        .pending()\
        .incomes()\
        .filter(due_date__lte=today)\
        .aggregate(Sum('value'))['value__sum']

def get_total_pending_expenses(user_id):
    today = date.today()
    return Transaction.objects\
        .owned_by(user_id)\
        .pending()\
        .expenses()\
        .filter(due_date__lte=today)\
        .aggregate(Sum('value'))['value__sum']

# TODO: Effective or not should be a query param
def get_effective_incomes_expenses_by_account(user_id):
    start, end = get_start_end_month(date.today())
    sum_when = lambda **kwargs : Coalesce(Sum(Case(When(then=F('value'), **kwargs), default=0)), 0) #TODO: move it somewhere else

    return Transaction.objects\
        .owned_by(user_id)\
        .payed()\
        .payed_between(start, end)\
        .values('account')\
        .annotate(
            incomes=sum_when(kind=HasKind.INCOME_KIND),
            expenses=sum_when(kind=HasKind.EXPENSE_KIND),
            total=Sum('value')
        )
        