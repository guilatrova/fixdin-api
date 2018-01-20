from transactions.models import Transaction, Category, BoundReasons, HasKind
from django.db import transaction as db_transaction
import datetime

@db_transaction.atomic
def create_transfer_between_accounts(from_id, to_id, user, **kwargs):
    kwargs['description'] = kwargs['bound_reason'] = BoundReasons.TRANSFER_BETWEEN_ACCOUNTS
    kwargs['payment_date'] = kwargs['due_date'] = datetime.datetime.today()
    kwargs['category'] = get_category(user)

    expense = Transaction.objects.create(account_id=from_id, kind=HasKind.EXPENSE_KIND, **kwargs)
    income = Transaction.objects.create(account_id=to_id, kind=HasKind.INCOME_KIND, bound_transaction=expense, **kwargs)
    expense.bound_transaction = income
    expense.save()

    return (expense, income)

def get_category(user):
    category, created = Category.objects.get_or_create(user=user, name='transfer_sys', defaults={
        'kind': HasKind.EXPENSE_KIND
    })

    return category