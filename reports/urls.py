from django.conf.urls import url
from transactions.models import Transaction
from reports import views

urlpatterns = [
    url(r'^last-months/$', views.LastMonthsAPIView.as_view(), name="last-months"),
    url(r'^pending-expenses/$', views.PendingAPIView.as_view(), name="pending-expenses", kwargs={'kind': Transaction.EXPENSE_KIND}),
    url(r'^pending-incomes/$', views.PendingAPIView.as_view(), name="pending-incomes", kwargs={'kind': Transaction.INCOME_KIND}),
    url(r'^values-by-category/(?P<kind>(expenses|incomes))/$', views.ValuesByCategoryAPIView.as_view(), name='values-by-category')
]