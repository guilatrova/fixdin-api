from django.db.models import QuerySet, Q

class TransactionsQuerySet(QuerySet):
    def owned_by(self, user):
        value = user if isinstance(user, int) else user.id
        return self.filter(account__user_id=value)

    def expires_between(self, from_date, until_date):
        return self.filter(due_date__gte=from_date, due_date__lte=until_date)
    
    def in_date_range(self, start, end):
        return self.filter(
            Q(due_date__gte=start, due_date__lte=end) |
            Q(payment_date__gte=start, payment_date__lte=end)
        )