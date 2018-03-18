from datetime import date
from django.db.models import Sum
from transactions.models import Transaction, HasKind

def get_total_pending_incomes(user_id):
    today = date.today()
    return Transaction.objects.filter(
        account__user_id=user_id, 
        kind=HasKind.INCOME_KIND,
        payment_date__isnull=True,
        due_date__gte=today
    ).aggregate(Sum('value'))['value__sum']
