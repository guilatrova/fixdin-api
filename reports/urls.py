from django.conf.urls import url
from transactions.models import Transaction
from reports import views

urlpatterns = [
    url(r'^last-13-months/$', views.Last13MonthsAPIView.as_view(), name="last-13-months"),
    url(r'^pending-expenses/$', views.PendingAPIView.as_view(), name="pending-expenses", kwargs={'kind': Transaction.EXPENSE_KIND}),
    url(r'^pending-incomes/$', views.PendingAPIView.as_view(), name="pending-incomes", kwargs={'kind': Transaction.INCOME_KIND}),
]