from django.conf.urls import url
from balances import views

#TODO: Refatorar aqui - Vários endpoints sem sentido
urlpatterns = [
    url(r'^current/$', views.get_balance, name="balances"),
    url(r'^detailed/accumulated/$', views.get_accumulated_balance, name="accumulated-balance"),
    url(r'^pending-incomes/$', views.get_total_pending_incomes, name="pending-incomes-balance"),
    url(r'^pending-expenses/$', views.get_total_pending_expenses, name="pending-expenses-balance"),
    #accounts
    url(r'^accounts/effective-incomes-expenses/$', views.get_effective_incomes_expenses_by_account, name="effective-incomes-expenses-balance-by-account"),
]