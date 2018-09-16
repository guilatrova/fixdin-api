import datetime

from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver

from transactions.models import Account, HasKind, Transaction
from transactions.reserved_categories import StartupAccountCategory


@receiver(pre_delete, sender=Transaction)
def updates_periodics_parent(sender, instance=None, **kwargs):
    if instance.bound_transaction_id == instance.id:

        next_parent = Transaction.objects\
            .exclude(id=instance.id)\
            .filter(bound_transaction_id=instance.id)\
            .order_by('due_date')\
            .first()

        if next_parent is not None:
            Transaction.objects.filter(bound_transaction_id=instance.id)\
                .update(bound_transaction_id=next_parent.id)


@receiver(post_save, sender=Account)
def creates_start_balance(sender, instance=None, created=False, **kwargs):
    if created:
        category, created = StartupAccountCategory.get_or_create(user_id=instance.user_id)
        value = instance.start_balance
        date = datetime.datetime.today()
        kind = HasKind.EXPENSE_KIND if value <= 0 else HasKind.INCOME_KIND

        Transaction.objects.create(
            account=instance,
            category=category,
            kind=kind,
            value=value,
            due_date=date,
            payment_date=date,
            description="STARTUP_ACCOUNT",
        )
