from django.db.models import QuerySet, Q

EXPENSE_KIND = 0
INCOME_KIND = 1
SIGNALS_WARNING_CONSENT = "IMPLEMENT THIS"

class TransactionsQuerySet(QuerySet):
    def owned_by(self, user):
        value = user if isinstance(user, int) else user.id
        return self.filter(account__user_id=value)

    def incomes(self):
        return self.filter(kind=INCOME_KIND)

    def expenses(self):
        return self.filter(kind=EXPENSE_KIND)

    def expires_between(self, from_date, until_date):
        return self.filter(due_date__gte=from_date, due_date__lte=until_date)

    def payed_between(self, from_date, until_date):
        return self.filter(payment_date__gte=from_date, payment_date__lte=until_date)

    def pending(self):
        return self.filter(payment_date__isnull=True)

    def payed(self):
        return self.filter(payment_date__isnull=False)

    # def delete(self, warning_consent):        
    #     pass TODO: IMPLEMENT THIS ALSO FOR UPDATE / CREATE
    
    def in_date_range(self, start, end):
        return self.filter(
            Q(due_date__gte=start, due_date__lte=end) |
            Q(payment_date__gte=start, payment_date__lte=end)
        )