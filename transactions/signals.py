from django.db.models.signals import pre_delete
from django.dispatch import receiver
from transactions.models import Transaction

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