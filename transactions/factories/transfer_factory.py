import datetime

from django.db import transaction as db_transaction

from transactions.models import BoundReasons, HasKind, Transaction
from transactions.reserved_categories import TransferCategory


@db_transaction.atomic
def create_transfer_between_accounts(user_id, **kwargs):
    from_id = kwargs.pop('account_from')
    to_id = kwargs.pop('account_to')
    value = kwargs.pop('value')
    kwargs['description'] = kwargs['bound_reason'] = BoundReasons.TRANSFER_BETWEEN_ACCOUNTS
    kwargs['payment_date'] = kwargs['due_date'] = datetime.datetime.today()
    kwargs['category'] = get_category(user_id)

    expense = Transaction.objects.create(account_id=from_id, value=-value, kind=HasKind.EXPENSE_KIND, **kwargs)
    income = Transaction.objects.create(account_id=to_id, value=value,
                                        kind=HasKind.INCOME_KIND, bound_transaction=expense, **kwargs)
    expense.bound_transaction = income
    expense.save()

    return (expense, income)


def get_category(user_id):
    category, created = TransferCategory.get_or_create(user_id=user_id)
    return category


def map_queryset_to_serializer_data(queryset):
    return [map_transaction_to_transfer_data(x) for x in queryset]


def map_transaction_to_transfer_data(expense):
    return {
        'id': expense.id,
        'account_from': expense.account.id,
        'account_to': expense.bound_transaction.account.id,
        'value': -expense.value
    }
