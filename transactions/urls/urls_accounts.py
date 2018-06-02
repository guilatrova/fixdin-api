from django.conf.urls import url

from transactions import views
from transactions.models import Account

list_actions = {
    'get': 'list', 
    'post': 'create'
}

single_action = {
    'get': 'retrieve',
    'put': 'update'
}

transfer_single_actions = {
    'get': 'retrieve',
    'put': 'update',
    'delete': 'destroy'
}

account_transfers_actions = {
    'get': 'list_from_account'
}

account_list = views.AccountViewSet.as_view(list_actions)
account_single = views.AccountViewSet.as_view(single_action)
account_transfers = views.TransferViewSet.as_view(account_transfers_actions)
transfer_list = views.TransferViewSet.as_view(list_actions)
transfer_single = views.TransferViewSet.as_view(transfer_single_actions)

urlpatterns = [
    url(r'^$', account_list, name='accounts'),
    url(r'^(?P<pk>\d+)$', account_single, name='account'),
    url(r'^(?P<pk>\d+)/transfers$', account_transfers, name='account-transfers'),
    url(r'^transfers$', transfer_list, name='transfers'),
    url(r'^transfers/(?P<pk>\d+)$', transfer_single, name='transfer'),
]
