from django.conf.urls import url
from balances import views

urlpatterns = [
    url(r'^current/$', views.get_balance, name="balances"),
    url(r'^pending-incomes/$', views.get_total_pending_incomes, name="pending-incomes-balance")
]