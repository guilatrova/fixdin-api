from django.db.models import Case, F, Sum, When
from django.db.models.functions import Coalesce, ExtractMonth, ExtractYear


def sum_when(**kwargs):
    return Coalesce(Sum(Case(When(then=F('value'), **kwargs), default=0)), 0)


def sum_effective(**kwargs):
    return sum_when(**kwargs, due_date__month=ExtractMonth('date'), due_date__year=ExtractYear('date'))


def sum_real(**kwargs):
    return sum_when(**kwargs,
                    payment_date__isnull=False,
                    payment_date__month=ExtractMonth('date'),
                    payment_date__year=ExtractYear('date'))


def sum_effective_kind(kind):
    return sum_effective(kind=kind)


def sum_real_kind(kind):
    return sum_real(kind=kind)
