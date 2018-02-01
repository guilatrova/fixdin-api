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

account_list = views.AccountViewSet.as_view(list_actions)
account_single = views.AccountViewSet.as_view(single_action)
transfer_list = views.TransferViewSet.as_view(list_actions)
transfer_single = views.TransferViewSet.as_view(transfer_single_actions)

urlpatterns = [
    #expenses
    url(r'^$', account_list, name='accounts'),
    url(r'^(?P<pk>\d+)$', account_single, name='account'),
    url(r'^transfers$', transfer_list, name='transfers'),
    url(r'^transfers/(?P<pk>\d+)$', transfer_single, name='transfer'),
]