from django.db.models import Sum, Case, When, F
from django.db.models.functions import Coalesce, TruncMonth, ExtractMonth, ExtractYear

sum_when = lambda **kwargs : Coalesce(Sum(Case(When(then=F('value'), **kwargs), default=0)), 0)
sum_effective = lambda **kwargs : sum_when(**kwargs, due_date__month=ExtractMonth('date'), due_date__year=ExtractYear('date'))
sum_real = lambda **kwargs : sum_when(**kwargs, payment_date__isnull=False, payment_date__month=ExtractMonth('date'), payment_date__year=ExtractYear('date'))
sum_effective_kind = lambda kind : sum_effective(kind=kind)
sum_real_kind = lambda kind : sum_real(kind=kind)