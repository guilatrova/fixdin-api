from transactions.models import Transaction, Category, BoundReasons, HasKind
from django.db import transaction as db_transaction
import datetime

@db_transaction.atomic
def create_transfer_between_accounts(from_id, to_id, user_id, **kwargs):
    kwargs['description'] = kwargs['bound_reason'] = BoundReasons.TRANSFER_BETWEEN_ACCOUNTS
    kwargs['payment_date'] = kwargs['due_date'] = datetime.datetime.today()
    kwargs['category'] = get_category(user_id)

    expense = Transaction.objects.create(account_id=from_id, kind=HasKind.EXPENSE_KIND, **kwargs)
    income = Transaction.objects.create(account_id=to_id, kind=HasKind.INCOME_KIND, bound_transaction=expense, **kwargs)
    expense.bound_transaction = income
    expense.save()

    return (expense, income)

def get_category(user_id):
    category, created = Category.objects.get_or_create(user_id=user_id, name='transfer_sys', defaults={
        'kind': HasKind.EXPENSE_KIND
    })

    return category

def map_queryset_to_serializer_data(queryset):
    data = []
    for transaction in queryset:
        entry = {
            'account_from': transaction.account.id,
            'account_to': transaction.bound_transaction.account.id,
            'value': transaction.value
        }
        data.append(entry)
    
    return data