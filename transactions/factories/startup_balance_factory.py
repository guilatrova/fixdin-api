import datetime

from transactions.models import HasKind, Transaction
from transactions.reserved_categories import StartupAccountCategory


def create_startup_transaction(account):
    category, created = StartupAccountCategory.get_or_create(user_id=account.user_id)
    value = account.start_balance
    date = datetime.datetime.today()
    kind = HasKind.EXPENSE_KIND if value <= 0 else HasKind.INCOME_KIND

    return Transaction.objects.create(
        account=account,
        category=category,
        kind=kind,
        value=value,
        due_date=date,
        payment_date=date,
        description=StartupAccountCategory.name,
    )
