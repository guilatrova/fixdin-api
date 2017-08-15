from django.conf.urls import url
from balances import views

urlpatterns = [
    url(r'^current/$', views.BalanceAPIView.as_view(), name="balances"),
]