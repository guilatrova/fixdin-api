from django.conf.urls import url
from transactions import views
from transactions.models import Account

list_actions = {
    'get': 'list', 
    'post': 'create'
}

single_action = {
    'get': 'retrieve',
    'put': 'update',
    'patch': 'partial_update',
    'delete': 'destroy'
}

account_list = views.AccountViewSet.as_view(list_actions)
account_single = views.AccountViewSet.as_view(single_action)

urlpatterns = [
    #expenses
    url(r'^$', account_list, name='accounts'),
    url(r'^(?P<pk>\d+)$', account_single, name='account'),
]