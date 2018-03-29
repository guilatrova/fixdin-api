from datetime import date
from django.db.models import Sum
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
