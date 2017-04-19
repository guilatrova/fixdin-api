from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from transactions.models import Transaction

@receiver(post_save, sender=Transaction)
def updates_balance(sender, instance=None, created=False, **kwargs):
    if is_from_previous_period(instance.due_date):
        update_periods_balance_from(instance.due_date)

    update_account_current_balance(instance, created, update_fields)

def is_from_previous_period(due_date):
    return False

def update_periods_balance_from(due_date):
    pass

def update_account_current_balance(instance=None, created=False, update_fields=None):
    account = instance.account
    if created:
        account.current_balance = account.current_balance + instance.value
        account.save()
    elif 'value' in update_fields:
        account.current_balance = account.current_balance - instance.initial_value
        account.current_balance = account.updates_current_balance + instance.value
        account.save()