from django.conf.urls import url
from balances import views

urlpatterns = [
    url(r'^plain/$', views.PlainBalanceAPIView.as_view(), name="plain-balance"),
    url(r'^detailed/$', views.DetailedBalanceAPIView.as_view(), name="detailed-balance"),
    #accounts
    url(r'^accounts/effective-incomes-expenses/$', views.get_effective_incomes_expenses_by_account, name="effective-incomes-expenses-balance-by-account"),
]