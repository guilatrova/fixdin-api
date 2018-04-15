from django.db.models import Sum, Case, When, F
from django.db.models.functions import Coalesce

sum_when = lambda **kwargs : Coalesce(Sum(Case(When(then=F('value'), **kwargs), default=0)), 0)