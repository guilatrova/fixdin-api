from django.db.models import QuerySet, Q

class TransactionsQuerySet(QuerySet):
    def in_date_range(self, start, end):
        return self.filter(
            Q(due_date__gte=start, due_date__lte=end) |
            Q(payment_date__gte=start, payment_date__lte=end)
        )