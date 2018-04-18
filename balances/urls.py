from django.conf.urls import url
from balances import views

urlpatterns = [
    url(r'^plain/$', views.PlainBalanceAPIView.as_view(), name="plain-balance"),
    url(r'^detailed/$', views.DetailedBalanceAPIView.as_view(), name="detailed-balance"),
    #accounts
    url(r'^accounts/detailed/$', views.DetailedAccountsBalanceAPIView.as_view(), name="detailed-balance-by-account"),
]